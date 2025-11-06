# TCP/IP Matrix Chat Application

A multi-user chat application built with Python that supports real-time messaging and matrix file operations over TCP/IP connections.

## 🌟 Features

- **Multi-user Chat**: Support for multiple simultaneous users
- **Real-time Messaging**: Instant message broadcasting to all connected clients
- **Matrix Operations**: Upload and process matrix files with various mathematical operations
- **File Support**: Handles both JSON and text format matrix files
- **Interactive Commands**: Rich command interface for matrix operations
- **User Management**: Username validation and user list display

## 🔧 Matrix Operations Supported

- **Addition**: Add multiple matrices
- **Subtraction**: Subtract one matrix from another
- **Multiplication**: Matrix multiplication
- **Transpose**: Matrix transposition
- **Determinant**: Calculate determinant of square matrices
- **Inverse**: Calculate matrix inverse
- **Eigenvalues**: Compute eigenvalues and eigenvectors
- **Display**: Format and display matrices

## 📋 Requirements

- Python 3.7+
- NumPy library

## 🚀 Installation

1. **Clone or download the project**:
   ```bash
   cd CNPROJECT
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Usage

### Starting the Server

Run the server first:
```bash
python server.py
```

The server will start on `localhost:12345` by default and wait for client connections.

### Connecting Clients

In separate terminals, run clients:
```bash
python client.py
```

Each client will prompt for:
- Server host (default: localhost)
- Server port (default: 12345)
- Username

### Chat Commands

Once connected, you can use these commands:

- **Regular messages**: Just type and press Enter
- **Help**: `/help` - Show all available commands
- **Send matrix file**: `/send <file_path>` - Upload and display matrix
- **Send with operation**: `/send <file_path> <operation>` - Upload and perform operation
- **Inline matrix operation**: `/matrix <operation> <matrix_data>`
- **Quit**: `/quit` - Leave the chat

### Matrix Input Formats

**File formats supported**:
- JSON: `[[1,2],[3,4]]`
- Text: 
  ```
  1 2
  3 4
  ```

**Inline format**:
- Single matrix: `1 2 3 | 4 5 6 | 7 8 9`
- Multiple matrices: `1 2 | 3 4 ; 5 6 | 7 8`

## 📁 Project Structure

```
CNPROJECT/
├── server.py              # Main chat server
├── client.py              # Chat client interface
├── matrix_operations.py   # Matrix processing module
├── requirements.txt       # Python dependencies
├── sample_matrices/       # Example matrix files
│   ├── matrix_3x3.json
│   ├── two_matrices_2x2.json
│   └── matrices_text.txt
└── README.md
```

## 🎮 Example Usage

1. **Start server**:
   ```bash
   python server.py
   ```

2. **Connect first client**:
   ```bash
   python client.py
   # Enter username: Alice
   ```

3. **Connect second client**:
   ```bash
   python client.py
   # Enter username: Bob
   ```

4. **Send messages**:
   ```
   Alice: Hello everyone!
   Bob: Hi Alice! Let's try some matrix operations.
   ```

5. **Upload matrix file**:
   ```
   Alice: /send sample_matrices/matrix_3x3.json transpose
   ```

6. **Perform inline operation**:
   ```
   Bob: /matrix add 1 2 | 3 4 ; 5 6 | 7 8
   ```

## 🔍 Matrix Operations Examples

### Single Matrix Operations
- `/send matrix.json transpose` - Transpose the matrix
- `/send matrix.json determinant` - Calculate determinant
- `/send matrix.json inverse` - Calculate inverse
- `/send matrix.json eigenvalues` - Find eigenvalues

### Two Matrix Operations  
- `/send matrices.json add` - Add matrices
- `/send matrices.json subtract` - Subtract matrices
- `/send matrices.json multiply` - Multiply matrices

### Inline Operations
```bash
# Add two 2x2 matrices
/matrix add 1 2 | 3 4 ; 5 6 | 7 8

# Transpose a 3x3 matrix
/matrix transpose 1 2 3 | 4 5 6 | 7 8 9
```

## 🛠️ Technical Details

- **Protocol**: TCP/IP sockets
- **Message Format**: JSON
- **Threading**: Multi-threaded server for concurrent clients
- **Matrix Library**: NumPy for efficient computations
- **Error Handling**: Comprehensive error handling for network and matrix operations

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License.
