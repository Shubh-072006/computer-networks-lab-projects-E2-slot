import { useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Calculator, Grid3x3, Clock, Upload } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import type { Matrix, MatrixOperationResult } from "@shared/schema";

interface MatrixOperationsProps {
  onExecute: (operation: string, matrixA: Matrix, matrixB?: Matrix) => Promise<MatrixOperationResult>;
}

export function MatrixOperations({ onExecute }: MatrixOperationsProps) {
  const [operation, setOperation] = useState<string>("add");
  const [rows, setRows] = useState<number>(3);
  const [cols, setCols] = useState<number>(3);
  const [matrixA, setMatrixA] = useState<number[][]>([]);
  const [matrixB, setMatrixB] = useState<number[][]>([]);
  const [result, setResult] = useState<MatrixOperationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const fileInputARef = useRef<HTMLInputElement>(null);
  const fileInputBRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const needsTwoMatrices = ['add', 'subtract', 'multiply'].includes(operation);

  const generateRandomMatrix = (r: number, c: number): number[][] => {
    return Array(r).fill(0).map(() =>
      Array(c).fill(0).map(() => Math.floor(Math.random() * 10))
    );
  };

  const handleGenerate = () => {
    const newMatrixA = generateRandomMatrix(rows, cols);
    setMatrixA(newMatrixA);
    if (needsTwoMatrices) {
      setMatrixB(generateRandomMatrix(rows, cols));
    }
  };

  const parseCSV = (content: string): number[][] | null => {
    try {
      const lines = content.trim().split('\n').filter(line => line.trim());
      if (lines.length === 0) {
        throw new Error("CSV file is empty");
      }

      const matrix: number[][] = [];
      let colCount: number | null = null;

      for (let i = 0; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        
        if (colCount === null) {
          colCount = values.length;
        } else if (values.length !== colCount) {
          throw new Error(`Row ${i + 1} has ${values.length} columns, expected ${colCount}`);
        }

        const row: number[] = [];
        for (let j = 0; j < values.length; j++) {
          const num = parseFloat(values[j]);
          if (isNaN(num)) {
            throw new Error(`Invalid number "${values[j]}" at row ${i + 1}, column ${j + 1}`);
          }
          row.push(num);
        }
        matrix.push(row);
      }

      if (matrix.length > 700 || (colCount && colCount > 700)) {
        throw new Error("Matrix dimensions exceed maximum of 700×700");
      }

      return matrix;
    } catch (error) {
      toast({
        title: "CSV Parse Error",
        description: error instanceof Error ? error.message : "Failed to parse CSV file",
        variant: "destructive",
      });
      return null;
    }
  };

  const handleFileUpload = (file: File, target: 'A' | 'B') => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      const matrix = parseCSV(content);
      if (matrix) {
        if (target === 'A') {
          setMatrixA(matrix);
          toast({
            title: "Matrix A Loaded",
            description: `Successfully loaded ${matrix.length}×${matrix[0].length} matrix`,
          });
        } else {
          setMatrixB(matrix);
          toast({
            title: "Matrix B Loaded",
            description: `Successfully loaded ${matrix.length}×${matrix[0].length} matrix`,
          });
        }
      }
    };
    reader.onerror = () => {
      toast({
        title: "File Read Error",
        description: "Failed to read the CSV file",
        variant: "destructive",
      });
    };
    reader.readAsText(file);
  };

  const handleExecute = async () => {
    if (matrixA.length === 0) return;
    
    setLoading(true);
    try {
      const matA: Matrix = {
        rows: matrixA.length,
        cols: matrixA[0].length,
        data: matrixA,
      };

      const matB: Matrix | undefined = needsTwoMatrices && matrixB.length > 0 ? {
        rows: matrixB.length,
        cols: matrixB[0].length,
        data: matrixB,
      } : undefined;

      const res = await onExecute(operation, matA, matB);
      setResult(res);
    } catch (error) {
      console.error("Matrix operation failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const renderMatrix = (matrix: number[][] | undefined, label: string) => {
    if (!matrix || matrix.length === 0) {
      return (
        <div className="text-sm text-muted-foreground text-center py-8 border border-dashed rounded-md">
          No matrix data. Click "Generate Random" to create one.
        </div>
      );
    }

    const displayRows = matrix.length <= 10 ? matrix : matrix.slice(0, 5);
    const displayCols = matrix[0].length <= 10 ? matrix[0].length : 10;

    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-sm font-medium">{label}</Label>
          <Badge variant="secondary" className="text-xs font-mono">
            {matrix.length} × {matrix[0].length}
          </Badge>
        </div>
        <div className="overflow-x-auto">
          <table className="border-collapse">
            <tbody>
              {displayRows.map((row, i) => (
                <tr key={i}>
                  {row.slice(0, displayCols).map((cell, j) => (
                    <td
                      key={j}
                      className="border border-border px-2 py-1 text-xs font-mono text-center min-w-[40px]"
                    >
                      {cell}
                    </td>
                  ))}
                  {matrix[0].length > 10 && (
                    <td className="px-2 text-xs text-muted-foreground">...</td>
                  )}
                </tr>
              ))}
              {matrix.length > 10 && (
                <tr>
                  <td colSpan={displayCols + 1} className="text-xs text-muted-foreground text-center py-1">
                    ... ({matrix.length - 5} more rows)
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderResult = () => {
    if (!result) return null;

    if (result.error) {
      return (
        <div className="text-sm text-destructive p-4 border border-destructive rounded-md">
          {result.error}
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Label className="text-sm font-medium">Result</Label>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs font-mono text-muted-foreground">
              {result.executionTime.toFixed(2)}ms
            </span>
          </div>
        </div>
        {typeof result.result === 'number' ? (
          <div className="p-4 border rounded-md bg-card">
            <span className="text-2xl font-bold font-mono">{result.result.toFixed(4)}</span>
          </div>
        ) : result.result ? (
          renderMatrix(result.result.data, "Result Matrix")
        ) : (
          <div className="text-sm text-muted-foreground">No result</div>
        )}
      </div>
    );
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Calculator className="w-5 h-5 text-primary" />
          <CardTitle className="text-xl font-semibold">Matrix Operations</CardTitle>
        </div>
        <CardDescription>
          Perform matrix operations up to 700×700 with real-time performance tracking
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="manual" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="random" data-testid="tab-random">Random</TabsTrigger>
            <TabsTrigger value="csv" data-testid="tab-csv">CSV Upload</TabsTrigger>
          </TabsList>
          
          <TabsContent value="manual" className="space-y-4 mt-4">
            <div className="text-sm text-muted-foreground">
              Manual input is available for matrices up to 10×10. For larger matrices, use Random Generation or CSV Upload.
            </div>
          </TabsContent>

          <TabsContent value="random" className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rows">Rows</Label>
                <Input
                  id="rows"
                  type="number"
                  min={1}
                  max={700}
                  value={rows}
                  onChange={(e) => setRows(parseInt(e.target.value) || 1)}
                  data-testid="input-rows"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="cols">Columns</Label>
                <Input
                  id="cols"
                  type="number"
                  min={1}
                  max={700}
                  value={cols}
                  onChange={(e) => setCols(parseInt(e.target.value) || 1)}
                  data-testid="input-cols"
                />
              </div>
            </div>
            <Button
              onClick={handleGenerate}
              variant="secondary"
              className="w-full"
              data-testid="button-generate"
            >
              <Grid3x3 className="w-4 h-4 mr-2" />
              Generate Random Matrices
            </Button>
          </TabsContent>

          <TabsContent value="csv" className="space-y-4 mt-4">
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">
                Upload CSV files with comma-separated numeric values. Each row should have the same number of columns. Maximum size: 700×700.
              </div>
              
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label>Matrix A</Label>
                  <input
                    ref={fileInputARef}
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFileUpload(file, 'A');
                      e.target.value = "";
                    }}
                    className="hidden"
                    data-testid="input-file-a"
                  />
                  <Button
                    onClick={() => fileInputARef.current?.click()}
                    variant="outline"
                    className="w-full"
                    data-testid="button-upload-a"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Matrix A CSV
                  </Button>
                </div>

                {needsTwoMatrices && (
                  <div className="space-y-2">
                    <Label>Matrix B</Label>
                    <input
                      ref={fileInputBRef}
                      type="file"
                      accept=".csv"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFileUpload(file, 'B');
                        e.target.value = "";
                      }}
                      className="hidden"
                      data-testid="input-file-b"
                    />
                    <Button
                      onClick={() => fileInputBRef.current?.click()}
                      variant="outline"
                      className="w-full"
                      data-testid="button-upload-b"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Matrix B CSV
                    </Button>
                  </div>
                )}
              </div>

              <div className="p-3 bg-muted rounded-md text-xs font-mono space-y-1">
                <div className="font-semibold text-foreground mb-2">CSV Format Example:</div>
                <div className="text-muted-foreground">1,2,3</div>
                <div className="text-muted-foreground">4,5,6</div>
                <div className="text-muted-foreground">7,8,9</div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <div className="space-y-2">
          <Label>Operation</Label>
          <Select value={operation} onValueChange={setOperation}>
            <SelectTrigger data-testid="select-operation">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="add">Addition</SelectItem>
              <SelectItem value="subtract">Subtraction</SelectItem>
              <SelectItem value="multiply">Multiplication</SelectItem>
              <SelectItem value="transpose">Transpose</SelectItem>
              <SelectItem value="determinant">Determinant</SelectItem>
              <SelectItem value="inverse">Inverse</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-4">
          {renderMatrix(matrixA, "Matrix A")}
          {needsTwoMatrices && renderMatrix(matrixB, "Matrix B")}
        </div>

        <Button
          onClick={handleExecute}
          disabled={loading || matrixA.length === 0}
          className="w-full"
          data-testid="button-execute"
        >
          <Calculator className="w-4 h-4 mr-2" />
          {loading ? "Executing..." : "Execute Operation"}
        </Button>

        {renderResult()}
      </CardContent>
    </Card>
  );
}
