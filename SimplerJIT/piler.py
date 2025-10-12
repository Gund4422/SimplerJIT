# piler.py
import ast

SIMD_OPS = {
    ast.Add: "_mm256_add_ps",
    ast.Sub: "_mm256_sub_ps",
    ast.Mult: "_mm256_mul_ps",
    ast.Div: "_mm256_div_ps",
}

SCALAR_OPS = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Mod: "%",
    ast.Pow: "**"
}

def generate_simd_c(array_names, n):
    """
    Generate SIMD C code for float32 arrays: a,b -> out
    Auto SIMD with remainder loop.
    """
    a, b, out = array_names
    c_code = f"""
#include <immintrin.h>
#include <stdio.h>

void simd_add(float* {a}, float* {b}, float* {out}, int n) {{
    int i;
    for(i = 0; i <= n-8; i+=8) {{
        __m256 va = _mm256_loadu_ps(&{a}[i]);
        __m256 vb = _mm256_loadu_ps(&{b}[i]);
        __m256 vc = _mm256_add_ps(va, vb);
        _mm256_storeu_ps(&{out}[i], vc);
    }}
    for(; i < n; i++) {{
        {out}[i] = {a}[i] + {b}[i];  // scalar fallback
    }}
}}

int main() {{
    int n = {n};
    float a[{n}], b[{n}], out[{n}];
    for(int i=0;i<n;i++){{ a[i]=i+1; b[i]=n-i; }}
    simd_add(a,b,out,n);
    for(int i=0;i<n;i++) printf("%f ", out[i]);
    return 0;
}}
"""
    return c_code
