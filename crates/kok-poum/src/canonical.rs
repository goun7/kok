// CANONICAL MATRICES emitted by g_layer_tests_en.py under random.seed(20260919).
// The Rust and Python sides must mine the SAME input or the benchmark
// comparison is not a comparison. Python's random.randrange is Mersenne
// Twister; Rust has no compatible generator in std, so the matrices are
// shipped as data rather than regenerated with a different PRNG.
pub const CANON_A: [[u64; 8]; 8] = [[81, 12, 44, 17, 83, 95, 43, 51], [92, 71, 35, 7, 8, 54, 11, 68], [2, 40, 75, 87, 3, 49, 0, 4], [86, 84, 63, 79, 29, 68, 3, 34], [70, 68, 21, 89, 16, 41, 60, 12], [12, 10, 0, 1, 26, 33, 19, 10], [92, 63, 46, 32, 1, 95, 54, 87], [80, 54, 72, 65, 89, 28, 13, 8]];
pub const CANON_B: [[u64; 8]; 8] = [[78, 10, 28, 23, 5, 56, 95, 28], [87, 23, 71, 73, 93, 60, 53, 23], [70, 96, 6, 68, 73, 39, 23, 23], [56, 4, 76, 92, 25, 15, 10, 84], [72, 77, 46, 68, 68, 10, 47, 8], [23, 52, 19, 38, 92, 71, 51, 96], [63, 25, 24, 10, 70, 43, 12, 82], [25, 39, 66, 39, 88, 28, 86, 24]];
