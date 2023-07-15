from llvmlite import ir
from llvmlite import binding as llvm

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# Define the LLVM IR for the memory operation counter
llvm_ir = """
define void @memop_counter() {
    %reads = alloca i32
    %writes = alloca i32
    store i32 0, i32* %reads
    store i32 0, i32* %writes

    ; Iterate over basic blocks in the function
    %entry = basicblock
    br label %entry

  entry:
    %counter = phi i32 [ 0, %entry ], [ %next_counter, %next_bb ]
    %next_counter = add i32 %counter, 1
    store i32 %next_counter, i32* %reads
    %next_bb = icmp eq i32 %next_counter, 10
    br i1 %next_bb, label %loop_end, label %entry

  loop_end:
    %next_bb_writes = add i32 %counter, 1
    store i32 %next_bb_writes, i32* %writes
    ret void
}
"""

# Create a new LLVM module and parse the LLVM IR
module = ir.Module()
module.triple = llvm.get_default_triple()
module.data_layout = ""

llvm_ir_module = llvm.parse_assembly(llvm_ir)
module.add_module(llvm_ir_module)

# Create a target machine
target_machine = llvm.Target.from_default_triple().create_target_machine()

# Optimize the module
pass_manager = llvm.ModulePassManager()
pass_manager.add_pass(llvm.PassManagerBuilder().populate())

pass_manager.run(module)

# Initialize the LLVM execution engine
execution_engine = llvm.create_mcjit_compiler(module, target_machine)

# Get a reference to the `memop_counter` function
memop_counter_fn = execution_engine.get_function_address("memop_counter")

# Run the memory operation counter function
memop_counter_fn()

# Retrieve the read and write counts from memory
reads = execution_engine.get_global_value_address("reads").inttoptr(ir.PointerType(ir.IntType(32)).as_pointer())
writes = execution_engine.get_global_value_address("writes").inttoptr(ir.PointerType(ir.IntType(32)).as_pointer())

# Print the results
print(f"Function memop_counter: reads = {reads[0]}; writes = {writes[0]}")
