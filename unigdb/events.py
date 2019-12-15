# ******* Hook types (from unicorn.h) *********************************************************************
# // All type of hooks for uc_hook_add() API.
# typedef enum uc_hook_type {
#    UC_HOOK_INTR = 1 << 0,   // Hook all interrupt/syscall events
#    UC_HOOK_INSN = 1 << 1,   // Hook a particular instruction
#    UC_HOOK_CODE = 1 << 2,   // Hook a range of code
#    UC_HOOK_BLOCK = 1 << 3,  // Hook basic blocks
#    UC_HOOK_MEM_READ_UNMAPPED = 1 << 4,   // Hook for memory read on unmapped memory
#    UC_HOOK_MEM_WRITE_UNMAPPED = 1 << 5,  // Hook for invalid memory write events
#    UC_HOOK_MEM_FETCH_UNMAPPED = 1 << 6,  // Hook for invalid memory fetch for execution events
#    UC_HOOK_MEM_READ_PROT = 1 << 7,   // Hook for memory read on read-protected memory
#    UC_HOOK_MEM_WRITE_PROT = 1 << 8,  // Hook for memory write on write-protected memory
#    UC_HOOK_MEM_FETCH_PROT = 1 << 9,  // Hook for memory fetch on non-executable memory
#   UC_HOOK_MEM_READ = 1 << 10,   // Hook memory read events.
#    UC_HOOK_MEM_WRITE = 1 << 11,  // Hook memory write events.
#    UC_HOOK_MEM_FETCH = 1 << 12,  // Hook memory fetch for execution events
# } uc_hook_type;
# *********************************************************************************************************


def hook_code(uc, address, size, user_data):
    pass


def hook_mem_access(uc, access, address, size, value, user_data):
    pass


def hook_intr(uc, except_idx, user_data):
    pass


def hook_block(uc, address, size, user_data):
    pass


def hook_insn(uc):
    pass
