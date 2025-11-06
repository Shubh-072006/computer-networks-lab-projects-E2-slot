"""
Matrix Operations Module
Handles various matrix operations for the chat server
"""

import numpy as np
import json
import re
from typing import List, Dict, Any


class MatrixProcessor:
    def __init__(self):
        self.supported_operations = {
            'add': self.add_matrices,
            'subtract': self.subtract_matrices,
            'multiply': self.multiply_matrices,
            'transpose': self.transpose_matrix,
            'determinant': self.determinant,
            'inverse': self.inverse_matrix,
            'eigenvalues': self.eigenvalues,
            'display': self.display_matrix
        }

    # ---------------- CORE LOGIC ---------------- #

    def process_matrix_data(self, matrix_data: str, operation: str = 'display') -> Dict[str, Any]:
        """Process matrix data from file content or direct input"""
        try:
            matrices = self.parse_matrix_data(matrix_data)

            if len(matrices) == 0:
                raise ValueError("No valid matrices found in the data")

            # Auto-correct operation type if mismatched
            if len(matrices) == 1 and operation in ['add', 'subtract', 'multiply']:
                operation = 'transpose'
            elif len(matrices) == 2 and operation in ['transpose', 'determinant', 'inverse', 'eigenvalues']:
                operation = 'add'

            result = self.perform_operation(operation, matrices)
            return result

        except Exception as e:
            raise Exception(f"Matrix processing error: {str(e)}")

    # ---------------- PARSING ---------------- #

    def parse_matrix_data(self, data: str) -> List[np.ndarray]:
        """Parse matrix data from various formats"""
        try:
            json_data = json.loads(data)
            matrices = []

            if isinstance(json_data, list) and len(json_data) > 0:
                if isinstance(json_data[0], list):
                    if isinstance(json_data[0][0], list):
                        # 3D array (list of matrices)
                        matrices = [np.array(m) for m in json_data]
                    else:
                        # 2D array (single matrix)
                        matrices = [np.array(json_data)]
                else:
                    matrices = [np.array([json_data])]
            else:
                matrices = [np.array([[json_data]])]

        except json.JSONDecodeError:
            # Try parsing plain text
            matrices = self.parse_text_matrices(data)

        return matrices

    def parse_text_matrices(self, text: str) -> List[np.ndarray]:
        """Parse matrices from text format"""
        matrices = []
        matrix_blocks = re.split(r'\n\s*\n|Matrix \d+:|matrix \d+:', text)

        for block in matrix_blocks:
            block = block.strip()
            if not block:
                continue

            rows = []
            for line in block.split('\n'):
                numbers = re.findall(r'-?\d+\.?\d*', line)
                if numbers:
                    rows.append([float(x) for x in numbers])

            if rows:
                max_cols = max(len(row) for row in rows)
                normalized = [row + [0.0] * (max_cols - len(row)) for row in rows]
                matrices.append(np.array(normalized))

        return matrices

    # ---------------- MAIN OPERATION CALLER ---------------- #

    def perform_operation(self, operation: str, matrices: List[Any]) -> Dict[str, Any]:
        """Perform the specified matrix operation with full NumPy normalization"""
        if operation not in self.supported_operations:
            raise ValueError(f"Unsupported operation: {operation}")

        # Convert every element safely to np.ndarray
        np_matrices = []
        for m in matrices:
            if isinstance(m, np.ndarray):
                np_matrices.append(m)
            elif isinstance(m, list):
                np_matrices.append(np.array(m))
            else:
                try:
                    np_matrices.append(np.array(m))
                except Exception:
                    raise ValueError(f"Invalid matrix type: {type(m)}")

        # Debug: show matrix shapes being processed
        print(f"[DEBUG] Performing '{operation}' on {[m.shape for m in np_matrices]}")

        try:
            result = self.supported_operations[operation](np_matrices)
            return result
        except Exception as e:
            raise Exception(f"Operation '{operation}' failed: {str(e)}")

    # ---------------- OPERATIONS ---------------- #

    def add_matrices(self, matrices: List[np.ndarray]) -> Dict[str, Any]:
        if len(matrices) < 2:
            raise ValueError("Addition requires at least 2 matrices")

        result = matrices[0].copy()
        for m in matrices[1:]:
            if result.shape != m.shape:
                raise ValueError(f"Matrix shapes don't match for addition: {result.shape} vs {m.shape}")
            result += m

        return {
            'matrix': result.tolist(),
            'shape': result.shape,
            'description': f"Sum of {len(matrices)} matrices"
        }

    def subtract_matrices(self, matrices: List[np.ndarray]) -> Dict[str, Any]:
        if len(matrices) != 2:
            raise ValueError("Subtraction requires exactly 2 matrices")

        a, b = matrices
        if a.shape != b.shape:
            raise ValueError(f"Matrix shapes don't match for subtraction: {a.shape} vs {b.shape}")

        result = a - b
        return {'matrix': result.tolist(), 'shape': result.shape, 'description': "Difference of matrices"}

    def multiply_matrices(self, matrices: List[np.ndarray]) -> Dict[str, Any]:
        if len(matrices) != 2:
            raise ValueError("Matrix multiplication requires exactly 2 matrices")

        a, b = matrices
        if a.shape[1] != b.shape[0]:
            raise ValueError(f"Cannot multiply matrices: {a.shape} × {b.shape}")

        result = np.dot(a, b)
        return {
            'matrix': result.tolist(),
            'shape': result.shape,
            'description': f"Product of {a.shape} and {b.shape} matrices"
        }

    def transpose_matrix(self, matrices: List[np.ndarray]) -> Dict[str, Any]:
        if len(matrices) != 1:
            raise ValueError("Transpose requires exactly 1 matrix")

        matrix = np.array(matrices[0])
        print(type(matrix))
        result = matrix.T
        return {
            'matrix': result.tolist(),
            'shape': result.shape,
            'description': f"Transpose of {matrix.shape} matrix"
        }

    def determinant(self, matrices: List[np.ndarray]) -> Dict[str, Any]:
        if len(matrices) != 1:
            raise ValueError("Determinant requires exactly 1 matrix")

        matrix = np.array(matrices[0])
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Determinant only valid for square matrices")

        det = np.linalg.det(matrix)
        return {'determinant': float(det), 'matrix': matrix.tolist(), 'description': f"Determinant of {matrix.shape}"}

    def inverse_matrix(self, matrices: List[np.ndarray]) -> Dict[str, Any]:
        if len(matrices) != 1:
            raise ValueError("Inverse requires exactly 1 matrix")

        matrix = np.array(matrices[0])
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Inverse only valid for square matrices")

        try:
            result = np.linalg.inv(matrix)
            return {
                'matrix': result.tolist(),
                'shape': result.shape,
                'description': f"Inverse of {matrix.shape} matrix"
            }
        except np.linalg.LinAlgError:
            raise ValueError("Matrix is singular and cannot be inverted")

    def eigenvalues(self, matrices: List[np.ndarray]) -> Dict[str, Any]:
        if len(matrices) != 1:
            raise ValueError("Eigenvalue calculation requires exactly 1 matrix")

        matrix = np.array(matrices[0])
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Eigenvalues only valid for square matrices")

        vals, vecs = np.linalg.eig(matrix)
        return {
            'eigenvalues': vals.tolist(),
            'eigenvectors': vecs.tolist(),
            'description': f"Eigenvalues and eigenvectors of {matrix.shape} matrix"
        }

    def display_matrix(self, matrices: List[np.ndarray]) -> Dict[str, Any]:
        results = []
        for i, m in enumerate(matrices):
            m = np.array(m)
            results.append({
                'matrix': m.tolist(),
                'shape': m.shape,
                'description': f"Matrix {i+1} ({m.shape[0]}×{m.shape[1]})"
            })

        return {
            'matrices': results,
            'count': len(matrices),
            'description': f"Displaying {len(matrices)} matrix(es)"
        }

    # ---------------- DISPLAY HELPER ---------------- #

    @staticmethod
    def format_matrix_for_display(matrix: np.ndarray) -> str:
        if not isinstance(matrix, np.ndarray):
            matrix = np.array(matrix)

        if matrix.size == 0:
            return "Empty matrix"

        rows = ["[" + " ".join(f"{val:8.3f}" for val in row) + "]" for row in matrix]
        return "\n".join(rows)