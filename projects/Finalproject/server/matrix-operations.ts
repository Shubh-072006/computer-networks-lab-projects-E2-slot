import type { Matrix } from "@shared/schema";

export class MatrixOperations {
  static add(a: Matrix, b: Matrix): Matrix {
    if (a.rows !== b.rows || a.cols !== b.cols) {
      throw new Error("Matrices must have the same dimensions for addition");
    }

    const result: number[][] = [];
    for (let i = 0; i < a.rows; i++) {
      result[i] = [];
      for (let j = 0; j < a.cols; j++) {
        result[i][j] = a.data[i][j] + b.data[i][j];
      }
    }

    return {
      rows: a.rows,
      cols: a.cols,
      data: result,
    };
  }

  static subtract(a: Matrix, b: Matrix): Matrix {
    if (a.rows !== b.rows || a.cols !== b.cols) {
      throw new Error("Matrices must have the same dimensions for subtraction");
    }

    const result: number[][] = [];
    for (let i = 0; i < a.rows; i++) {
      result[i] = [];
      for (let j = 0; j < a.cols; j++) {
        result[i][j] = a.data[i][j] - b.data[i][j];
      }
    }

    return {
      rows: a.rows,
      cols: a.cols,
      data: result,
    };
  }

  static multiply(a: Matrix, b: Matrix): Matrix {
    if (a.cols !== b.rows) {
      throw new Error("Number of columns in first matrix must equal number of rows in second matrix");
    }

    const result: number[][] = [];
    for (let i = 0; i < a.rows; i++) {
      result[i] = [];
      for (let j = 0; j < b.cols; j++) {
        let sum = 0;
        for (let k = 0; k < a.cols; k++) {
          sum += a.data[i][k] * b.data[k][j];
        }
        result[i][j] = sum;
      }
    }

    return {
      rows: a.rows,
      cols: b.cols,
      data: result,
    };
  }

  static transpose(a: Matrix): Matrix {
    const result: number[][] = [];
    for (let i = 0; i < a.cols; i++) {
      result[i] = [];
      for (let j = 0; j < a.rows; j++) {
        result[i][j] = a.data[j][i];
      }
    }

    return {
      rows: a.cols,
      cols: a.rows,
      data: result,
    };
  }

  static determinant(a: Matrix): number {
    if (a.rows !== a.cols) {
      throw new Error("Matrix must be square to calculate determinant");
    }

    const n = a.rows;

    if (n === 1) {
      return a.data[0][0];
    }

    if (n === 2) {
      return a.data[0][0] * a.data[1][1] - a.data[0][1] * a.data[1][0];
    }

    let det = 0;
    for (let j = 0; j < n; j++) {
      const minor = this.getMinor(a, 0, j);
      det += (j % 2 === 0 ? 1 : -1) * a.data[0][j] * this.determinant(minor);
    }

    return det;
  }

  static inverse(a: Matrix): Matrix {
    if (a.rows !== a.cols) {
      throw new Error("Matrix must be square to calculate inverse");
    }

    const det = this.determinant(a);
    if (Math.abs(det) < 1e-10) {
      throw new Error("Matrix is singular and cannot be inverted");
    }

    const n = a.rows;
    const adjugate = this.adjugate(a);
    const result: number[][] = [];

    for (let i = 0; i < n; i++) {
      result[i] = [];
      for (let j = 0; j < n; j++) {
        result[i][j] = adjugate.data[i][j] / det;
      }
    }

    return {
      rows: n,
      cols: n,
      data: result,
    };
  }

  private static getMinor(a: Matrix, row: number, col: number): Matrix {
    const result: number[][] = [];
    for (let i = 0; i < a.rows; i++) {
      if (i === row) continue;
      const newRow: number[] = [];
      for (let j = 0; j < a.cols; j++) {
        if (j === col) continue;
        newRow.push(a.data[i][j]);
      }
      result.push(newRow);
    }

    return {
      rows: a.rows - 1,
      cols: a.cols - 1,
      data: result,
    };
  }

  private static adjugate(a: Matrix): Matrix {
    const n = a.rows;
    const result: number[][] = [];

    for (let i = 0; i < n; i++) {
      result[i] = [];
      for (let j = 0; j < n; j++) {
        const minor = this.getMinor(a, i, j);
        const cofactor = ((i + j) % 2 === 0 ? 1 : -1) * this.determinant(minor);
        result[i][j] = cofactor;
      }
    }

    return this.transpose({
      rows: n,
      cols: n,
      data: result,
    });
  }
}
