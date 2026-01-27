/**
 * Metal GPU accelerated GF(2^16) matrix echelonization
 *
 * Compile:
 *   clang++ -std=c++17 -O3 -framework Metal -framework Foundation -fobjc-arc \
 * echelon_gpu.mm -o echelon
 */

#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

#include <chrono>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using namespace std;

static NSString *metalShaderSource = @R"(
#include <metal_stdlib>
using namespace metal;

// x^16 + x^5 + x^3 + x^2 + 1
constant uint GF_POLY = 0x1002D;
constant uint GF_MASK = 0xFFFF;

// Multiply two elements in GF(2^16)
inline uint gf_mul(uint a, uint b) {
    uint result = 0;
    while (b) {
        if (b & 1) {
            result ^= a;
        }
        b >>= 1;
        a <<= 1;
        if (a & 0x10000) {
            a ^= GF_POLY;
        }
    }
    return result & GF_MASK;
}

// a^(-1) = a^(2^16 - 2) in GF(2^16)
inline uint gf_inv(uint a) {
    if (a == 0) return 0;

    uint result = 1;
    uint base = a;
    uint exp = 0xFFFE; // 2^16 - 2

    while (exp > 0) {
        if (exp & 1) {
            result = gf_mul(result, base);
        }
        base = gf_mul(base, base);
        exp >>= 1;
    }
    return result;
}

// Kernel: Find pivot in column (reduction to find non-zero element)
kernel void find_pivot(
    device const ushort* matrix [[buffer(0)]],
    volatile device atomic_uint* pivot_row [[buffer(1)]],
    constant uint& col [[buffer(2)]],
    constant uint& start_row [[buffer(3)]],
    constant uint& num_rows [[buffer(4)]],
    constant uint& num_cols [[buffer(5)]],
    uint tid [[thread_position_in_grid]]
) {
    uint row = start_row + tid;
    if (row >= num_rows) return;

    uint idx = row * num_cols + col;
    if (matrix[idx] != 0) {
        atomic_fetch_min_explicit(pivot_row, row, memory_order_relaxed);
    }
}

// Kernel: Swap two rows
kernel void swap_rows(
    device ushort* matrix [[buffer(0)]],
    constant uint& row1 [[buffer(1)]],
    constant uint& row2 [[buffer(2)]],
    constant uint& num_cols [[buffer(3)]],
    uint tid [[thread_position_in_grid]]
) {
    if (tid >= num_cols) return;

    uint idx1 = row1 * num_cols + tid;
    uint idx2 = row2 * num_cols + tid;

    ushort tmp = matrix[idx1];
    matrix[idx1] = matrix[idx2];
    matrix[idx2] = tmp;
}

// Kernel: Scale a row by the inverse of its pivot element
kernel void scale_row(
    device ushort* matrix [[buffer(0)]],
    constant uint& row [[buffer(1)]],
    constant uint& pivot_col [[buffer(2)]],
    constant uint& num_cols [[buffer(3)]],
    uint tid [[thread_position_in_grid]]
) {
    if (tid >= num_cols) return;

    uint pivot_idx = row * num_cols + pivot_col;
    uint inv = gf_inv(matrix[pivot_idx]);

    uint idx = row * num_cols + tid;
    matrix[idx] = gf_mul(matrix[idx], inv);
}

// Kernel: row reduction
// Each thread handles one row
kernel void eliminate_column(
    device ushort* matrix [[buffer(0)]],
    constant uint& pivot_row [[buffer(1)]],
    constant uint& pivot_col [[buffer(2)]],
    constant uint& num_rows [[buffer(3)]],
    constant uint& num_cols [[buffer(4)]],
    uint row [[thread_position_in_grid]]
) {
    if (row >= num_rows || row == pivot_row) return;

    uint factor_idx = row * num_cols + pivot_col;
    uint factor = matrix[factor_idx];

    if (factor == 0) return;

    for (uint col = 0; col < num_cols; col++) {
        uint pivot_idx = pivot_row * num_cols + col;
        uint idx = row * num_cols + col;
        matrix[idx] ^= gf_mul(factor, matrix[pivot_idx]);
    }
}

// Kernel: Eliminate column entries
kernel void eliminate_column_parallel(
    device ushort* matrix [[buffer(0)]],
    device const ushort* pivot_row_data [[buffer(1)]],
    device const ushort* factors [[buffer(2)]],
    constant uint& pivot_row [[buffer(3)]],
    constant uint& num_rows [[buffer(4)]],
    constant uint& num_cols [[buffer(5)]],
    uint2 tid [[thread_position_in_grid]]
) {
    uint row = tid.x;
    uint col = tid.y;

    if (row >= num_rows || col >= num_cols || row == pivot_row) return;

    uint factor = factors[row];
    if (factor == 0) return;

    uint idx = row * num_cols + col;
    matrix[idx] ^= gf_mul(factor, pivot_row_data[col]);
}

// Kernel: Extract factors for elimination
kernel void extract_factors(
    device const ushort* matrix [[buffer(0)]],
    device ushort* factors [[buffer(1)]],
    constant uint& pivot_col [[buffer(2)]],
    constant uint& num_rows [[buffer(3)]],
    constant uint& num_cols [[buffer(4)]],
    uint row [[thread_position_in_grid]]
) {
    if (row >= num_rows) return;
    factors[row] = matrix[row * num_cols + pivot_col];
}

// Kernel: Copy pivot row to buffer
kernel void copy_pivot_row(
    device const ushort* matrix [[buffer(0)]],
    device ushort* pivot_row_data [[buffer(1)]],
    constant uint& pivot_row [[buffer(2)]],
    constant uint& num_cols [[buffer(3)]],
    uint col [[thread_position_in_grid]]
) {
    if (col >= num_cols) return;
    pivot_row_data[col] = matrix[pivot_row * num_cols + col];
}
)";

class MetalGF2E {
private:
  id<MTLDevice> device;
  id<MTLCommandQueue> commandQueue;
  id<MTLLibrary> library;
  id<MTLComputePipelineState> findPivotPipeline;
  id<MTLComputePipelineState> swapRowsPipeline;
  id<MTLComputePipelineState> scaleRowPipeline;
  id<MTLComputePipelineState> eliminateColumnPipeline;
  id<MTLComputePipelineState> eliminateParallelPipeline;
  id<MTLComputePipelineState> extractFactorsPipeline;
  id<MTLComputePipelineState> copyPivotRowPipeline;

  id<MTLBuffer> matrixBuffer;
  id<MTLBuffer> pivotRowBuffer;
  id<MTLBuffer> pivotRowDataBuffer;
  id<MTLBuffer> factorsBuffer;

  uint32_t numRows;
  uint32_t numCols;

  id<MTLComputePipelineState> createPipeline(NSString *functionName) {
    NSError *error = nil;
    id<MTLFunction> function = [library newFunctionWithName:functionName];
    if (!function) {
      cerr << "Failed to find function: " << [functionName UTF8String] << endl;
      exit(1);
    }
    id<MTLComputePipelineState> pipeline =
        [device newComputePipelineStateWithFunction:function error:&error];
    if (!pipeline) {
      cerr << "Failed to create pipeline for: " << [functionName UTF8String]
           << endl;
      if (error) {
        cerr << [[error localizedDescription] UTF8String] << endl;
      }
      exit(1);
    }
    return pipeline;
  }

public:
  MetalGF2E() {
    device = MTLCreateSystemDefaultDevice();
    if (!device) {
      cerr << "Metal is not supported on this device" << endl;
      exit(1);
    }

    commandQueue = [device newCommandQueue];

    // Compile shader
    NSError *error = nil;
    library = [device newLibraryWithSource:metalShaderSource
                                   options:nil
                                     error:&error];
    if (!library) {
      cerr << "Failed to compile Metal shaders" << endl;
      if (error) {
        cerr << [[error localizedDescription] UTF8String] << endl;
      }
      exit(1);
    }

    // Create pipelines
    findPivotPipeline = createPipeline(@"find_pivot");
    swapRowsPipeline = createPipeline(@"swap_rows");
    scaleRowPipeline = createPipeline(@"scale_row");
    eliminateColumnPipeline = createPipeline(@"eliminate_column");
    eliminateParallelPipeline = createPipeline(@"eliminate_column_parallel");
    extractFactorsPipeline = createPipeline(@"extract_factors");
    copyPivotRowPipeline = createPipeline(@"copy_pivot_row");

    matrixBuffer = nil;
    pivotRowBuffer = nil;
    pivotRowDataBuffer = nil;
    factorsBuffer = nil;
  }

  void loadMatrix(const vector<uint16_t> &data, uint32_t rows, uint32_t cols) {
    numRows = rows;
    numCols = cols;

    size_t matrixSize = rows * cols * sizeof(uint16_t);
    matrixBuffer = [device newBufferWithBytes:data.data()
                                       length:matrixSize
                                      options:MTLResourceStorageModeShared];

    pivotRowBuffer = [device newBufferWithLength:sizeof(uint32_t)
                                         options:MTLResourceStorageModeShared];
    pivotRowDataBuffer =
        [device newBufferWithLength:cols * sizeof(uint16_t)
                            options:MTLResourceStorageModeShared];
    factorsBuffer = [device newBufferWithLength:rows * sizeof(uint16_t)
                                        options:MTLResourceStorageModeShared];
  }

  void echelonize() {
    uint32_t pivotCol = 0;

    for (uint32_t pivotRow = 0; pivotRow < numRows && pivotCol < numCols;) {
      uint32_t *pivotPtr = (uint32_t *)[pivotRowBuffer contents];
      *pivotPtr = UINT32_MAX;

      @autoreleasepool {
        id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];
        id<MTLComputeCommandEncoder> encoder =
            [commandBuffer computeCommandEncoder];

        [encoder setComputePipelineState:findPivotPipeline];
        [encoder setBuffer:matrixBuffer offset:0 atIndex:0];
        [encoder setBuffer:pivotRowBuffer offset:0 atIndex:1];
        [encoder setBytes:&pivotCol length:sizeof(uint32_t) atIndex:2];
        [encoder setBytes:&pivotRow length:sizeof(uint32_t) atIndex:3];
        [encoder setBytes:&numRows length:sizeof(uint32_t) atIndex:4];
        [encoder setBytes:&numCols length:sizeof(uint32_t) atIndex:5];

        uint32_t searchRows = numRows - pivotRow;
        MTLSize gridSize = MTLSizeMake(searchRows, 1, 1);
        MTLSize threadGroupSize = MTLSizeMake(min(256u, searchRows), 1, 1);
        [encoder dispatchThreads:gridSize
            threadsPerThreadgroup:threadGroupSize];

        [encoder endEncoding];
        [commandBuffer commit];
        [commandBuffer waitUntilCompleted];
      }

      uint32_t foundPivotRow = *pivotPtr;

      if (foundPivotRow == UINT32_MAX) {
        // No pivot found in this column, move to next column
        pivotCol++;
        continue;
      }

      // Swap rows if necessary
      if (foundPivotRow != pivotRow) {
        @autoreleasepool {
          id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];
          id<MTLComputeCommandEncoder> encoder =
              [commandBuffer computeCommandEncoder];

          [encoder setComputePipelineState:swapRowsPipeline];
          [encoder setBuffer:matrixBuffer offset:0 atIndex:0];
          [encoder setBytes:&pivotRow length:sizeof(uint32_t) atIndex:1];
          [encoder setBytes:&foundPivotRow length:sizeof(uint32_t) atIndex:2];
          [encoder setBytes:&numCols length:sizeof(uint32_t) atIndex:3];

          MTLSize gridSize = MTLSizeMake(numCols, 1, 1);
          MTLSize threadGroupSize = MTLSizeMake(min(256u, numCols), 1, 1);
          [encoder dispatchThreads:gridSize
              threadsPerThreadgroup:threadGroupSize];

          [encoder endEncoding];
          [commandBuffer commit];
          [commandBuffer waitUntilCompleted];
        }
      }

      // Scale pivot row
      @autoreleasepool {
        id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];
        id<MTLComputeCommandEncoder> encoder =
            [commandBuffer computeCommandEncoder];

        [encoder setComputePipelineState:scaleRowPipeline];
        [encoder setBuffer:matrixBuffer offset:0 atIndex:0];
        [encoder setBytes:&pivotRow length:sizeof(uint32_t) atIndex:1];
        [encoder setBytes:&pivotCol length:sizeof(uint32_t) atIndex:2];
        [encoder setBytes:&numCols length:sizeof(uint32_t) atIndex:3];

        MTLSize gridSize = MTLSizeMake(numCols, 1, 1);
        MTLSize threadGroupSize = MTLSizeMake(min(256u, numCols), 1, 1);
        [encoder dispatchThreads:gridSize
            threadsPerThreadgroup:threadGroupSize];

        [encoder endEncoding];
        [commandBuffer commit];
        [commandBuffer waitUntilCompleted];
      }

      bool useParallel = (numRows > 256 && numCols > 256);

      if (useParallel) {
        // Extract factors and copy pivot row
        @autoreleasepool {
          id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];

          // Extract factors
          {
            id<MTLComputeCommandEncoder> encoder =
                [commandBuffer computeCommandEncoder];
            [encoder setComputePipelineState:extractFactorsPipeline];
            [encoder setBuffer:matrixBuffer offset:0 atIndex:0];
            [encoder setBuffer:factorsBuffer offset:0 atIndex:1];
            [encoder setBytes:&pivotCol length:sizeof(uint32_t) atIndex:2];
            [encoder setBytes:&numRows length:sizeof(uint32_t) atIndex:3];
            [encoder setBytes:&numCols length:sizeof(uint32_t) atIndex:4];

            MTLSize gridSize = MTLSizeMake(numRows, 1, 1);
            MTLSize threadGroupSize = MTLSizeMake(min(256u, numRows), 1, 1);
            [encoder dispatchThreads:gridSize
                threadsPerThreadgroup:threadGroupSize];
            [encoder endEncoding];
          }

          {
            id<MTLComputeCommandEncoder> encoder =
                [commandBuffer computeCommandEncoder];
            [encoder setComputePipelineState:copyPivotRowPipeline];
            [encoder setBuffer:matrixBuffer offset:0 atIndex:0];
            [encoder setBuffer:pivotRowDataBuffer offset:0 atIndex:1];
            [encoder setBytes:&pivotRow length:sizeof(uint32_t) atIndex:2];
            [encoder setBytes:&numCols length:sizeof(uint32_t) atIndex:3];

            MTLSize gridSize = MTLSizeMake(numCols, 1, 1);
            MTLSize threadGroupSize = MTLSizeMake(min(256u, numCols), 1, 1);
            [encoder dispatchThreads:gridSize
                threadsPerThreadgroup:threadGroupSize];
            [encoder endEncoding];
          }

          [commandBuffer commit];
          [commandBuffer waitUntilCompleted];
        }

        // elimination
        @autoreleasepool {
          id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];
          id<MTLComputeCommandEncoder> encoder =
              [commandBuffer computeCommandEncoder];

          [encoder setComputePipelineState:eliminateParallelPipeline];
          [encoder setBuffer:matrixBuffer offset:0 atIndex:0];
          [encoder setBuffer:pivotRowDataBuffer offset:0 atIndex:1];
          [encoder setBuffer:factorsBuffer offset:0 atIndex:2];
          [encoder setBytes:&pivotRow length:sizeof(uint32_t) atIndex:3];
          [encoder setBytes:&numRows length:sizeof(uint32_t) atIndex:4];
          [encoder setBytes:&numCols length:sizeof(uint32_t) atIndex:5];

          MTLSize gridSize = MTLSizeMake(numRows, numCols, 1);
          MTLSize threadGroupSize = MTLSizeMake(16, 16, 1);
          [encoder dispatchThreads:gridSize
              threadsPerThreadgroup:threadGroupSize];

          [encoder endEncoding];
          [commandBuffer commit];
          [commandBuffer waitUntilCompleted];
        }
      } else {
        // Row-based elimination for smaller matrices
        @autoreleasepool {
          id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];
          id<MTLComputeCommandEncoder> encoder =
              [commandBuffer computeCommandEncoder];

          [encoder setComputePipelineState:eliminateColumnPipeline];
          [encoder setBuffer:matrixBuffer offset:0 atIndex:0];
          [encoder setBytes:&pivotRow length:sizeof(uint32_t) atIndex:1];
          [encoder setBytes:&pivotCol length:sizeof(uint32_t) atIndex:2];
          [encoder setBytes:&numRows length:sizeof(uint32_t) atIndex:3];
          [encoder setBytes:&numCols length:sizeof(uint32_t) atIndex:4];

          MTLSize gridSize = MTLSizeMake(numRows, 1, 1);
          MTLSize threadGroupSize = MTLSizeMake(min(256u, numRows), 1, 1);
          [encoder dispatchThreads:gridSize
              threadsPerThreadgroup:threadGroupSize];

          [encoder endEncoding];
          [commandBuffer commit];
          [commandBuffer waitUntilCompleted];
        }
      }

      pivotRow++;
      pivotCol++;
    }
  }

  void getMatrix(vector<uint16_t> &data) {
    uint16_t *ptr = (uint16_t *)[matrixBuffer contents];
    data.assign(ptr, ptr + numRows * numCols);
  }
};

// Read matrix from file
bool readMatrix(const string &filename, vector<uint16_t> &data, uint64_t &rows,
                uint64_t &cols) {
  ifstream f(filename, ios::binary);
  if (!f.is_open()) {
    cerr << "Failed to open '" << filename << "'" << endl;
    return false;
  }

  f.read(reinterpret_cast<char *>(&rows), sizeof(rows));
  f.read(reinterpret_cast<char *>(&cols), sizeof(cols));

  cout << "Matrix size: " << rows << " x " << cols << endl;

  data.resize(rows * cols);

  // Read each GF2E element (stored as 8 bytes, but only lower 16 bits used)
  for (uint64_t i = 0; i < rows * cols; i++) {
    uint64_t val;
    f.read(reinterpret_cast<char *>(&val), 8);
    data[i] = val & 0xFFFF;
  }

  f.close();
  return true;
}

// Write matrix to file
bool writeMatrix(const string &filename, const vector<uint16_t> &data,
                 uint64_t rows, uint64_t cols) {
  ofstream f(filename, ios::binary);
  if (!f.is_open()) {
    cerr << "Failed to open '" << filename << "'" << endl;
    return false;
  }

  f.write(reinterpret_cast<const char *>(&rows), sizeof(rows));
  f.write(reinterpret_cast<const char *>(&cols), sizeof(cols));

  // Write each element as 8 bytes
  for (uint64_t i = 0; i < rows * cols; i++) {
    uint64_t val = data[i];
    f.write(reinterpret_cast<const char *>(&val), 8);
  }

  f.close();
  return true;
}

int main(int argc, char *argv[]) {
  @autoreleasepool {
    if (argc != 2) {
      cerr << "Usage: " << argv[0] << " <filename>" << endl;
      return 1;
    }

    string filename = argv[1];

    vector<uint16_t> data;
    uint64_t rows, cols;
    if (!readMatrix(filename, data, rows, cols)) {
      return 1;
    }

    MetalGF2E metal;
    metal.loadMatrix(data, (uint32_t)rows, (uint32_t)cols);

    cout << "Starting echelonization..." << endl;
    auto start = chrono::high_resolution_clock::now();

    metal.echelonize();

    auto end = chrono::high_resolution_clock::now();
    auto duration = chrono::duration_cast<chrono::milliseconds>(end - start);
    cout << "Echelonization completed in " << duration.count() << " ms" << endl;

    metal.getMatrix(data);
    if (!writeMatrix(filename, data, rows, cols)) {
      return 1;
    }

    cout << "Result written to " << filename << endl;
    return 0;
  }
}
