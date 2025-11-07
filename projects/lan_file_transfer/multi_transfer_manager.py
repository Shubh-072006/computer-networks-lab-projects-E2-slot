"""
Multi-File, Multi-User Transfer Manager
Handles concurrent file transfers to multiple servers with queue management
"""

import os
import json
import threading
import time
import queue
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from client import FileTransferSession
from utils import setup_logging, format_file_size


class TransferStatus(Enum):
    """Transfer status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TransferTask:
    """Represents a single file transfer task"""
    id: str
    filename: str
    file_path: str
    file_size: int
    target_server: str
    target_port: int
    password: str
    status: TransferStatus = TransferStatus.PENDING
    progress: float = 0.0
    sent_bytes: int = 0
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    transfer_session: Optional[FileTransferSession] = None


@dataclass
class BatchTransfer:
    """Represents a batch of file transfers"""
    id: str
    name: str
    files: List[TransferTask]
    target_servers: List[Dict[str, any]]
    status: TransferStatus = TransferStatus.PENDING
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class MultiTransferManager:
    """
    Manages multiple concurrent file transfers to multiple servers
    """
    
    def __init__(self, max_concurrent_transfers: int = 5):
        """
        Initialize the multi-transfer manager
        
        Args:
            max_concurrent_transfers (int): Maximum number of concurrent transfers
        """
        self.max_concurrent_transfers = max_concurrent_transfers
        self.logger = setup_logging()
        
        # Transfer management
        self.transfer_queue = queue.Queue()
        self.active_transfers: Dict[str, TransferTask] = {}
        self.completed_transfers: List[TransferTask] = []
        self.batch_transfers: Dict[str, BatchTransfer] = {}
        
        # Worker threads
        self.worker_threads: List[threading.Thread] = []
        self.running = False
        
        # Callbacks
        self.on_transfer_started: Optional[Callable] = None
        self.on_transfer_progress: Optional[Callable] = None
        self.on_transfer_completed: Optional[Callable] = None
        self.on_batch_completed: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            'total_transfers': 0,
            'successful_transfers': 0,
            'failed_transfers': 0,
            'total_bytes_transferred': 0,
            'average_transfer_speed': 0.0
        }
    
    def start(self) -> None:
        """Start the transfer manager and worker threads"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker threads
        for i in range(self.max_concurrent_transfers):
            worker = threading.Thread(target=self._worker_thread, name=f"TransferWorker-{i}")
            worker.daemon = True
            worker.start()
            self.worker_threads.append(worker)
        
        self.logger.info(f"Multi-transfer manager started with {self.max_concurrent_transfers} worker threads")
    
    def stop(self) -> None:
        """Stop the transfer manager and all worker threads"""
        self.running = False
        
        # Cancel all pending transfers
        while not self.transfer_queue.empty():
            try:
                task = self.transfer_queue.get_nowait()
                task.status = TransferStatus.CANCELLED
                self.completed_transfers.append(task)
            except queue.Empty:
                break
        
        # Wait for worker threads to finish
        for worker in self.worker_threads:
            worker.join(timeout=5)
        
        self.worker_threads.clear()
        self.logger.info("Multi-transfer manager stopped")
    
    def add_batch_transfer(self, name: str, files: List[str], target_servers: List[Dict[str, any]], 
                          password: str = "lan_transfer_2024") -> str:
        """
        Add a batch transfer with multiple files to multiple servers
        
        Args:
            name (str): Name for the batch transfer
            files (List[str]): List of file paths to transfer
            target_servers (List[Dict]): List of target servers with 'ip' and 'port' keys
            password (str): Authentication password
            
        Returns:
            str: Batch transfer ID
        """
        batch_id = f"batch_{int(time.time() * 1000)}"
        transfer_tasks = []
        
        # Create transfer tasks for each file to each server
        for file_path in files:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                continue
            
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            for server in target_servers:
                task_id = f"{batch_id}_{filename}_{server['ip']}_{server['port']}"
                
                task = TransferTask(
                    id=task_id,
                    filename=filename,
                    file_path=file_path,
                    file_size=file_size,
                    target_server=server['ip'],
                    target_port=server['port'],
                    password=password
                )
                
                transfer_tasks.append(task)
        
        # Create batch transfer
        batch = BatchTransfer(
            id=batch_id,
            name=name,
            files=transfer_tasks,
            target_servers=target_servers,
            created_at=time.time()
        )
        
        self.batch_transfers[batch_id] = batch
        
        # Add tasks to queue
        for task in transfer_tasks:
            self.transfer_queue.put(task)
            self.stats['total_transfers'] += 1
        
        self.logger.info(f"Added batch transfer '{name}' with {len(transfer_tasks)} tasks")
        
        if self.on_batch_completed:
            self.on_batch_completed(batch)
        
        return batch_id
    
    def add_single_transfer(self, file_path: str, target_server: str, target_port: int, 
                           password: str = "lan_transfer_2024") -> str:
        """
        Add a single file transfer
        
        Args:
            file_path (str): Path to file to transfer
            target_server (str): Target server IP
            target_port (int): Target server port
            password (str): Authentication password
            
        Returns:
            str: Transfer task ID
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        task_id = f"single_{int(time.time() * 1000)}"
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        task = TransferTask(
            id=task_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            target_server=target_server,
            target_port=target_port,
            password=password
        )
        
        self.transfer_queue.put(task)
        self.stats['total_transfers'] += 1
        
        self.logger.info(f"Added single transfer: {filename} to {target_server}:{target_port}")
        
        return task_id
    
    def cancel_transfer(self, task_id: str) -> bool:
        """
        Cancel a transfer task
        
        Args:
            task_id (str): Transfer task ID
            
        Returns:
            bool: True if cancelled successfully
        """
        # Check if task is in active transfers
        if task_id in self.active_transfers:
            task = self.active_transfers[task_id]
            task.status = TransferStatus.CANCELLED
            
            # Disconnect the transfer session
            if task.transfer_session:
                task.transfer_session.client.disconnect()
            
            # Move to completed
            self.completed_transfers.append(task)
            del self.active_transfers[task_id]
            
            self.logger.info(f"Cancelled transfer: {task.filename}")
            return True
        
        return False
    
    def get_transfer_status(self, task_id: str) -> Optional[TransferTask]:
        """
        Get status of a specific transfer
        
        Args:
            task_id (str): Transfer task ID
            
        Returns:
            Optional[TransferTask]: Transfer task or None if not found
        """
        # Check active transfers
        if task_id in self.active_transfers:
            return self.active_transfers[task_id]
        
        # Check completed transfers
        for task in self.completed_transfers:
            if task.id == task_id:
                return task
        
        return None
    
    def get_all_transfers(self) -> Dict[str, any]:
        """
        Get status of all transfers
        
        Returns:
            Dict: Summary of all transfers
        """
        return {
            'active_transfers': len(self.active_transfers),
            'completed_transfers': len(self.completed_transfers),
            'queue_size': self.transfer_queue.qsize(),
            'batch_transfers': len(self.batch_transfers),
            'statistics': self.stats.copy(),
            'transfers': {
                'active': [self._task_to_dict(task) for task in self.active_transfers.values()],
                'completed': [self._task_to_dict(task) for task in self.completed_transfers[-50:]]  # Last 50
            }
        }
    
    def _worker_thread(self) -> None:
        """Worker thread that processes transfer tasks"""
        while self.running:
            try:
                # Get next task from queue
                task = self.transfer_queue.get(timeout=1)
                
                # Check if task was cancelled
                if task.status == TransferStatus.CANCELLED:
                    self.transfer_queue.task_done()
                    continue
                
                # Start transfer
                self._execute_transfer(task)
                
                # Mark task as done
                self.transfer_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker thread error: {e}")
                if self.on_error:
                    self.on_error(f"Worker error: {e}")
    
    def _execute_transfer(self, task: TransferTask) -> None:
        """
        Execute a single transfer task
        
        Args:
            task (TransferTask): Transfer task to execute
        """
        try:
            # Update task status
            task.status = TransferStatus.IN_PROGRESS
            task.start_time = time.time()
            self.active_transfers[task.id] = task
            
            self.logger.info(f"Starting transfer: {task.filename} to {task.target_server}:{task.target_port}")
            
            if self.on_transfer_started:
                self.on_transfer_started(task)
            
            # Create transfer session
            session = FileTransferSession(task.password)
            task.transfer_session = session
            
            # Set up callbacks
            def on_progress(progress, sent, total):
                task.progress = progress
                task.sent_bytes = sent
                
                if self.on_transfer_progress:
                    self.on_transfer_progress(task)
            
            def on_complete(filename, size, success):
                task.end_time = time.time()
                
                if success:
                    task.status = TransferStatus.COMPLETED
                    self.stats['successful_transfers'] += 1
                    self.stats['total_bytes_transferred'] += size
                    
                    # Calculate transfer speed
                    duration = task.end_time - task.start_time
                    if duration > 0:
                        speed = size / duration
                        task.transfer_speed = speed
                else:
                    task.status = TransferStatus.FAILED
                    self.stats['failed_transfers'] += 1
                
                # Move to completed
                self.completed_transfers.append(task)
                if task.id in self.active_transfers:
                    del self.active_transfers[task.id]
                
                if self.on_transfer_completed:
                    self.on_transfer_completed(task)
            
            def on_error(error_message):
                task.status = TransferStatus.FAILED
                task.error_message = error_message
                task.end_time = time.time()
                
                self.stats['failed_transfers'] += 1
                
                # Move to completed
                self.completed_transfers.append(task)
                if task.id in self.active_transfers:
                    del self.active_transfers[task.id]
                
                if self.on_error:
                    self.on_error(f"Transfer error: {error_message}")
            
            session.set_callbacks(
                on_progress=on_progress,
                on_complete=on_complete,
                on_error=on_error
            )
            
            # Execute transfer
            success = session.connect_and_send_file(
                task.target_server,
                task.target_port,
                task.file_path
            )
            
            # Final status update
            if not success and task.status == TransferStatus.IN_PROGRESS:
                task.status = TransferStatus.FAILED
                task.end_time = time.time()
                self.stats['failed_transfers'] += 1
                
                # Move to completed
                self.completed_transfers.append(task)
                if task.id in self.active_transfers:
                    del self.active_transfers[task.id]
        
        except Exception as e:
            self.logger.error(f"Transfer execution error: {e}")
            task.status = TransferStatus.FAILED
            task.error_message = str(e)
            task.end_time = time.time()
            
            self.stats['failed_transfers'] += 1
            
            # Move to completed
            self.completed_transfers.append(task)
            if task.id in self.active_transfers:
                del self.active_transfers[task.id]
            
            if self.on_error:
                self.on_error(f"Transfer execution error: {e}")
    
    def _task_to_dict(self, task: TransferTask) -> Dict[str, any]:
        """Convert TransferTask to dictionary for JSON serialization"""
        return {
            'id': task.id,
            'filename': task.filename,
            'file_size': task.file_size,
            'file_size_formatted': format_file_size(task.file_size),
            'target_server': f"{task.target_server}:{task.target_port}",
            'status': task.status.value,
            'progress': task.progress,
            'sent_bytes': task.sent_bytes,
            'sent_bytes_formatted': format_file_size(task.sent_bytes),
            'error_message': task.error_message,
            'start_time': task.start_time,
            'end_time': task.end_time,
            'duration': (task.end_time - task.start_time) if task.start_time and task.end_time else None
        }


# Global instance
transfer_manager = MultiTransferManager()
