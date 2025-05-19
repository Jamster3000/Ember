INSTRUCTION_CATEGORIES = {
    "data_transfer": [
        # x86/x86-64 data movement instructions
        "mov", "movs", "cmov", "cmova", "cmovae", "cmovb", "cmovbe", "cmovc", "cmove", "cmovg", "cmovge",
        "cmovl", "cmovle", "cmovna", "cmovnae", "cmovnb", "cmovnbe", "cmovnc", "cmovne", "cmovng", "cmovnge",
        "cmovnl", "cmovnle", "cmovno", "cmovnp", "cmovns", "cmovnz", "cmovo", "cmovp", "cmovpe", "cmovpo",
        "cmovs", "cmovz", "movzx", "movsx", "movsxd", "movsb", "movsw", "movsd", "movsq", "bswap", 
        "xadd", "xchg", "cmpxchg", "cmpxchg8b", "cmpxchg16b", "cld", "std", "lodsb", "lodsw", "lodsd", "lodsq", 
        "stosb", "stosw", "stosd", "stosq", "fld", "fst", "fstp", "fxch",
        
        # 16-bit specific x86
        "pusha", "popa", "pushf", "popf", "lahf", "sahf", "xlat",
        
        # 32-bit specific x86
        "pushad", "popad", "pushfd", "popfd",
        
        # 64-bit specific x86-64
        "pushfq", "popfq", "swapgs", "rdtscp", "cqo",

        # ARM data movement
        "ldr", "str", "ldrb", "strb", "ldm", "stm", "ldmia", "ldmib", "ldmda", "ldmdb", 
        "stmia", "stmib", "stmda", "stmdb", "push", "pop", "vldr", "vstr", "vldm", "vstm", 
        "vpush", "vpop", "ldrex", "strex", "swp", "ldrd", "strd", "ldrh", "strh", 
        "ldrsb", "ldrsh", "stp", "ldp", "mov", "mvn", "movt", "movw",
        
        # ARM 64-bit specific (AArch64)
        "ldp", "stp", "ldnp", "stnp", "ldtr", "sttr", "ldur", "stur", "prfm",
        
        # MIPS data movement
        "lw", "sw", "lb", "sb", "lh", "sh", "lwl", "lwr", "swl", "swr", "ulw", "usw", 
        "ll", "sc", "lwc1", "swc1", "move", "movz", "movn",
        
        # PowerPC data movement
        "lbz", "lhz", "lwz", "lha", "lwzx", "stwx", "stbx", "sthx", "lmw", "stmw", 
        "lwarx", "stwcx", "ld", "std", "ldu", "stdu", "lwa",
        
        # RISC-V data movement
        "lw", "sw", "lb", "sb", "lh", "sh", "lbu", "lhu", "lwu", "ld", "sd", "flw", "fsw", "fld", "fsd",
        
        # 6502/65C02 (8-bit)
        "lda", "sta", "ldx", "stx", "ldy", "sty", "tax", "tay", "txa", "tya", 
        
        # Z80 (8-bit)
        "ld", "ldi", "ldir", "ldd", "lddr", "ex", "exx", "push", "pop", "in", "out",
        
        # Generic data movement
        "memcpy", "memset", "memcmp", "in", "out", "movq", "ld", "st", "ld.b", "st.b", 
        "get", "put", "fetch", "store", "exchange", "swap", "transfer"
    ],
    
    # Arithmetic instructions across architectures
    "arithmetic": [
        # x86/x86-64 arithmetic
        "add", "adc", "sub", "sbb", "mul", "imul", "div", "idiv", "inc", "dec", "neg", 
        "lea", "daa", "das", "aam", "aad", "cbw", "cwd", "cdq", "cdqe", "cqo", "sal", "sar", "rol", "ror", 
        "rcl", "rcr", "shl", "shr", "shld", "shrd", "bsf", "bsr", "popcnt", 
        "fadd", "fsub", "fmul", "fdiv", "fiadd", "fisub", "fimul", "fidiv", "fprem",

        # 16-bit specific x86
        "aas", "aaa",
        
        # 32/64-bit x86 extensions
        "adcx", "adox", "mulx", "bzhi", "pdep", "pext",
        
        # ARM arithmetic
        "add", "adc", "sub", "rsb", "rsc", "mul", "mla", "mls", "umull", "smull", 
        "smulh", "umulh", "smlal", "umlal", "udiv", "sdiv", "qadd", "qsub", 
        "sadd", "ssub", "vadd", "vsub", "vmul", "vdiv", "vneg", "vabs",
        
        # ARM 64-bit specific
        "madd", "msub", "mneg", "smaddl", "smsubl", "umaddl", "umsubl", "ror",
        
        # MIPS arithmetic
        "add", "addu", "addi", "addiu", "sub", "subu", "mult", "multu", "div", "divu", 
        "madd", "msub", "mfhi", "mflo", "mthi", "mtlo", "lui", "clo", "clz",
        
        # PowerPC arithmetic
        "add", "addc", "adde", "addme", "addze", "addi", "addic", "addis", "subf", 
        "subfc", "subfe", "subfme", "subfze", "subfic", "mulli", "mullw", "mulhw", 
        "mulhwu", "divw", "divwu", "divdu", "modud", "extsb", "extsw",
        
        # RISC-V arithmetic
        "add", "addi", "sub", "lui", "auipc", "mul", "mulh", "mulhu", "mulhsu", "div", "divu", "rem", "remu",
        
        # 6502/65C02 arithmetic
        "adc", "sbc", "inc", "dec", "inx", "dex", "iny", "dey",
        
        # Z80 arithmetic
        "add", "adc", "sub", "sbc", "inc", "dec", "daa", "cpl", "neg", "scf", "ccf",
        
        # Generic arithmetic terms
        "negate", "invert", "flip", "bitrev", "count", "abs", "sign", "increment", 
        "decrement", "multiply", "divide", "modulo", "remainder", "square", "cube"
    ],
    
    # Comparison/logic instructions
    "comparison": [
        # x86/x86-64 comparison/logic
        "cmp", "test", "and", "or", "xor", "not", "bt", "bts", "btr", "btc",
        "seta", "setae", "setb", "setbe", "setc", "sete", "setg", "setge", "setl", "setle",
        "setna", "setnae", "setnb", "setnbe", "setnc", "setne", "setng", "setnge", "setnl",
        "setnle", "setno", "setnp", "setns", "setnz", "seto", "setp", "setpe", "setpo", "sets", "setz",
        "fcmp", "pcmp", "pcmpeq", "pcmpgt", "ptest",
        
        # ARM comparison/logic
        "cmp", "cmn", "tst", "teq", "and", "orr", "eor", "bic", "orn", "mvn", 
        "tsteq", "tstne", "teq", "subs", "cmphs", "cmpeq", "cmpne",
        
        # MIPS comparison/logic
        "and", "andi", "or", "ori", "xor", "xori", "nor", "slt", "sltu", "slti", 
        "sltiu", "sge", "sgeu", "sgt", "sgtu",
        
        # PowerPC comparison/logic
        "and", "andi", "andis", "or", "ori", "oris", "xor", "xori", "xoris",
        "cmpl", "cmpi", "cmp", "fcmpu", "andc", "orc", "nand", "eqv", "nabs",
        
        # RISC-V comparison/logic  
        "and", "andi", "or", "ori", "xor", "xori", "slt", "slti", "sltu", "sltiu",
        
        # 6502/65C02 comparison/logic
        "cmp", "cpx", "cpy", "and", "ora", "eor", "bit",
        
        # Z80 comparison/logic
        "cp", "and", "or", "xor", "bit", "set", "res", "rlca", "rrca", "rla", "rra",
        
        # Generic comparison terms
        "equal", "notequal", "greater", "less", "mask", "match", "select", 
        "extract", "insert", "compare", "evaluate", "check"
    ],
    
    # Control flow instructions
    "jump": [
        # x86/x86-64 jumps
        "jmp", "je", "jz", "jne", "jnz", "jg", "jge", "jl", "jle", "ja", "jae", "jb", "jbe",
        "jc", "jnc", "jo", "jno", "js", "jns", "jecxz", "jrcxz", "loop", "loope", "loopne",
        
        # ARM branches/jumps
        "b", "bl", "bx", "blx", "bgt", "bge", "blt", "ble", "beq", "bne", "bhs", "blo", 
        "bmi", "bpl", "bvs", "bvc", "bal", "cbz", "cbnz",
        
        # MIPS jumps
        "j", "jr", "beq", "bne", "blez", "bgtz", "bltz", "bltzal", "bgez", "bgezal",
        
        # PowerPC branches
        "b", "bc", "bca", "bcl", "bcla", "bdnz", "bdnzt", "bdnzf", "bdz", "bdzt", 
        "bdzf", "bcctr", "bclr",
        
        # RISC-V branches
        "beq", "bne", "blt", "bge", "bltu", "bgeu", "j", "jal", "jalr",
        
        # 6502/65C02 branches
        "bpl", "bmi", "bvc", "bvs", "bcc", "bcs", "bne", "beq", "brk", "jmp", "jsr", "rts",
        
        # Z80 jumps
        "jp", "jr", "djnz", "call", "ret", "reti", "retn",
        
        # Generic control flow
        "break", "divert", "skip", "repeat", "until", "while", "for", "next", "continue",
        "goto", "branch", "fork", "choice", "switch", "case"
    ],
    
    # Function calls and related instructions
    "call": [
        # x86/x86-64 calls
        "call", "ret", "syscall", "int", "into", "iret", "iretd", "iretq", "sysenter", 
        "sysexit", "sysret", "enter", "leave", "bound",
        
        # ARM calls
        "bl", "blx", "svc", "swi", "blr", "ret", "bxlr", "pop {lr}", "mov pc, lr", "bx lr",
        
        # MIPS calls
        "jal", "jalr", "syscall", "break", "eret",
        
        # PowerPC calls
        "bl", "sc", "rfi", "rfid",
        
        # RISC-V calls
        "jal", "jalr", "ecall", "ebreak", "ret",
        
        # 6502/65C02 calls
        "jsr", "rts", "brk", "rti",
        
        # Z80 calls
        "call", "ret", "reti", "retn", "rst",
        
        # Generic call terms
        "invoke", "trap", "signal", "callback", "yield", "resume", "enter", "exit", "return"
    ],
    
    # SIMD/vector operations across architectures
    "simd": [
        # x86/x86-64 MMX/SSE/AVX
        # MMX
        "movq", "paddb", "paddw", "paddd", "paddsb", "paddsw", "paddusb", "paddusw",
        "psubb", "psubw", "psubd", "psubsb", "psubsw", "psubusb", "psubusw",
        "pmulhw", "pmullw", "pmaddwd",
        # SSE/SSE2
        "movaps", "movups", "movss", "addps", "subps", "mulps", "divps", "movapd", "movupd",
        "movsd", "addpd", "subpd", "mulpd", "divpd", "pand", "por", "pxor", "pandn",
        "paddq", "psubq", "pmaddwd", "pshufd", "pshufb", "pslld", "psrld", "psllq", "psrlq",
        # AVX/AVX2/AVX-512
        "vmovaps", "vmovapd", "vaddps", "vaddpd", "vsubps", "vsubpd", "vmulps", "vmulpd",
        "vdivps", "vdivpd", "vblendps", "vblendpd", "vperm2f128", "vbroadcastss", "vbroadcastsd",
        "vfmadd132ps", "vfmadd213ps", "vfmadd231ps", "vfmadd132pd", "vfmadd213pd", "vfmadd231pd",
        "vgatherdps", "vgatherdpd", "vscatterdps", "vscatterdpd",
        
        # ARM NEON
        "vadd", "vsub", "vmul", "vdiv", "vld1", "vst1", "vld2", "vst2", "vld3", "vst3", "vld4", "vst4",
        "vmov", "vdup", "vrev", "vzip", "vuzp", "vtrn", "vswp", "vabs", "vneg", "vqadd", "vqsub", 
        "vmla", "vmls", "vpadd", "vceq", "vcgt", "vcge", "vclt", "vcle", "vmax", "vmin", "vqdmulh",
        # ARMv8 Advanced SIMD
        "fmla", "fmls", "fadd", "fsub", "fmul", "fdiv", "fmax", "fmin", "frecpe", "frecps",
        
        # PowerPC Altivec/VMX
        "lvx", "stvx", "vperm", "vsel", "vmaddfp", "vmladduhm", "vaddubm", "vadduhm", 
        "vadduwm", "vsububm", "vsubuhm", "vsubuwm", "vmaxub", "vmaxuh", "vmaxuw",
        "vmaxsb", "vmaxsh", "vmaxsw", "vminub", "vminuh", "vminuw", "vminsb", "vminsh", "vminsw",
        
        # RISC-V Vector Extensions
        "vsetvli", "vsetvl", "vle", "vse", "vle8", "vse8", "vle16", "vse16", "vle32",
        "vse32", "vle64", "vse64", "vadd", "vsub", "vmul", "vdiv", "vmacc", "vmsac",
        
        # Generic vector/SIMD
        "pack", "unpack", "shuffle", "blend", "broadcast", "permute", "transpose",
        "insert", "extract", "interleave", "deinterleave", "reduce", "expand"
    ],
    
    # Bit manipulation instructions
    "bitwise": [
        # x86/x86-64 bit manipulation
        "and", "or", "xor", "not", "neg", "shl", "shr", "sar", "sal", "rol", "ror", "rcl", "rcr",
        "bsf", "bsr", "bswap", "bt", "btc", "btr", "bts", "popcnt", "tzcnt", "lzcnt",
        # BMI1/BMI2 (Bit Manipulation Instructions)
        "andn", "blsi", "blsmsk", "blsr", "pdep", "pext", "bzhi",
        # TBM (Trailing Bit Manipulation)
        "bextr", "blcfill", "blci", "blcic", "blcmsk", "blcs", "blsfill", "blsic", "t1mskc", "tzmsk",
        
        # ARM bit manipulation
        "and", "orr", "eor", "bic", "orn", "mvn", "clz", "rbit", "rev", "rev16", "revsh", "ubfx", "sbfx",
        "bfc", "bfi", "sbfx", "ubfx", "bfxil", "sbfiz", "ubfiz",
        
        # MIPS bit manipulation
        "and", "or", "xor", "nor", "sll", "srl", "sra", "sllv", "srlv", "srav", "ext", "ins", "wsbh", 
        "bitrev", "msb", "lsb", "rotr", "rotrv",
        
        # PowerPC bit manipulation
        "and", "andc", "or", "orc", "xor", "nand", "nor", "eqv", "slw", "srw", "sraw", "rldcl", 
        "rldcr", "rldic", "rldicl", "rldicr", "rlwinm", "rlwnm", "rlwimi",
        
        # RISC-V bit manipulation
        "and", "or", "xor", "sll", "srl", "sra", "slli", "srli", "srai", "andn", "orn",
        "xnor", "clz", "ctz", "pcnt", "bext", "bdep", "grev", "gorc", "shfl", "unshfl",
        
        # 6502/65C02 bit manipulation
        "and", "ora", "eor", "asl", "lsr", "rol", "ror", "bit", "trb", "tsb",
        
        # Z80 bit manipulation
        "and", "or", "xor", "cpl", "bit", "set", "res", "rl", "rr", "rlc", "rrc", "sla", "sra", "srl",
        
        # Generic bit operations
        "shift", "rotate", "extract", "insert", "count", "swap", "reverse", "mask",
        "isolate", "clear", "toggle", "test"
    ],
    
    # Floating-point operations
    "floating_point": [
        # x86/x86-64 x87 FPU
        "fadd", "fsub", "fmul", "fdiv", "fsqrt", "fsin", "fcos", "ftan", "fabs", "fchs", "ftst",
        "fld", "fst", "fstp", "fild", "fist", "fistp", "fcomip", "fucomip", "fldcw", "fnstcw",
        "fldenv", "fstenv", "fsave", "frstor", "finit", "fninit", "fclex", "fnclex", 
        "fxam", "fldz", "fld1", "fldpi", "frndint", "fscale", "fxtract", "fprem", "fprem1", "fptan",
        "fpatan", "f2xm1", "fyl2x", "fyl2xp1",
        
        # x86/x86-64 SSE/SSE2/AVX floating point
        "addss", "subss", "mulss", "divss", "sqrtss", "minss", "maxss", "addsd", "subsd", 
        "mulsd", "divsd", "sqrtsd", "minsd", "maxsd", "addps", "subps", "mulps", "divps",
        "sqrtps", "minps", "maxps", "addpd", "subpd", "mulpd", "divpd", "sqrtpd", "minpd", "maxpd",
        "cvtss2sd", "cvtsd2ss", "cvtsi2ss", "cvtsi2sd", "cvttss2si", "cvttsd2si",
        "ucomiss", "ucomisd", "comiss", "comisd", "roundss", "roundsd", "roundps", "roundpd",
        
        # ARM floating point
        "vadd.f32", "vsub.f32", "vmul.f32", "vdiv.f32", "vsqrt.f32", "vcmp.f32",
        "vadd.f64", "vsub.f64", "vmul.f64", "vdiv.f64", "vsqrt.f64", "vcmp.f64",
        "vcvt.f32.s32", "vcvt.s32.f32", "vcvt.f64.f32", "vcvt.f32.f64", 
        "vminnm", "vmaxnm", "vrinta", "vrintm", "vrintn", "vrintp", "vrintx", "vrintz",
        
        # MIPS floating point
        "add.s", "sub.s", "mul.s", "div.s", "sqrt.s", "abs.s", "neg.s", "c.eq.s", "c.lt.s", "c.le.s",
        "add.d", "sub.d", "mul.d", "div.d", "sqrt.d", "abs.d", "neg.d", "c.eq.d", "c.lt.d", "c.le.d",
        "cvt.s.d", "cvt.d.s", "cvt.s.w", "cvt.d.w", "cvt.w.s", "cvt.w.d",
        
        # PowerPC floating point
        "fadd", "fsub", "fmul", "fdiv", "fsqrt", "fabs", "fneg", "fcmp", "fsel", 
        "fsqrts", "fres", "frsqrte", "fre", "fmadd", "fmsub", "fnmadd", "fnmsub", "fctiw", "fctiwz",
        
        # RISC-V floating point
        "fadd.s", "fsub.s", "fmul.s", "fdiv.s", "fsqrt.s", "fmin.s", "fmax.s", "feq.s", "flt.s", "fle.s",
        "fadd.d", "fsub.d", "fmul.d", "fdiv.d", "fsqrt.d", "fmin.d", "fmax.d", "feq.d", "flt.d", "fle.d",
        "fcvt.w.s", "fcvt.s.w", "fcvt.wu.s", "fcvt.s.wu", "fcvt.w.d", "fcvt.d.w", "fcvt.wu.d", "fcvt.d.wu",
        "fclass.s", "fclass.d", "fmadd.s", "fmsub.s", "fnmsub.s", "fnmadd.s",
        
        # Generic floating point
        "ceil", "floor", "round", "trunc", "exponent", "mantissa", "normalize", "denormalize",
        "float", "double", "precision", "nan", "infinity", "subnormal"
    ],
    
    # System and privileged instructions
    "system": [
        # x86/x86-64 system
        "cli", "sti", "hlt", "nop", "pause", "ud2", "rdmsr", "wrmsr", "rdtsc", "rdtscp", "rdpmc",
        "lgdt", "sgdt", "lidt", "sidt", "lldt", "sldt", "ltr", "str", "clflush", "clflushopt", "clwb",
        "invd", "invlpg", "wbinvd", "cpuid", "monitor", "mwait", "xgetbv", "xsetbv",
        # x86 virtualization
        "vmcall", "vmlaunch", "vmresume", "vmxoff", "vmxon", "vmptrld", "vmptrst", "vmclear", "vmread", "vmwrite",
        
        # ARM system
        "mrs", "msr", "cpsid", "cpsie", "dsb", "dmb", "isb", "wfi", "wfe", "sev", "clrex",
        # ARM exception
        "svc", "hvc", "smc", "bkpt",
        # ARM virtualization
        "eret", "mrc", "mcr", "mrrc", "mcrr",
        
        # MIPS system
        "mfc0", "mtc0", "cache", "sync", "synci", "wait", "eret", "di", "ei",
        
        # PowerPC system
        "mtspr", "mfspr", "mtmsr", "mfmsr", "tlbie", "tlbia", "tlbsync", "isync", "sync", "eieio", "dcbf",
        
        # RISC-V system
        "csrrw", "csrrs", "csrrc", "csrrwi", "csrrsi", "csrrci", "fence", "fence.i", "sfence.vma",
        "wfi", "mret", "sret", "uret",
        
        # Generic system
        "lock", "unlock", "fence", "barrier", "serialize", "flush", "invalidate", "halt", "sleep", "wake"
    ],
    
    # String operations
    "string": [
        # x86/x86-64 string
        "movs", "movsb", "movsw", "movsd", "movsq", "cmps", "cmpsb", "cmpsw", "cmpsd", "cmpsq",
        "scas", "scasb", "scasw", "scasd", "scasq", "lods", "lodsb", "lodsw", "lodsd", "lodsq",
        "stos", "stosb", "stosw", "stosd", "stosq", "rep", "repe", "repne", "repz", "repnz",
        
        # ARM string (pseudo-instructions or function names)
        "memcpy", "memset", "memcmp", "strcmp", "strcpy",
        
        # Generic string
        "copy", "compare", "find", "scan", "load", "store", "search", "replace",
        "length", "index", "fill", "clear", "trim", "pad"
    ],
    
    # Cryptographic instructions
    "crypto": [
        # x86/x86-64 AES-NI
        "aesenc", "aesenclast", "aesdec", "aesdeclast", "aesimc", "aeskeygenassist",
        # x86/x86-64 SHA
        "sha1msg1", "sha1msg2", "sha1nexte", "sha1rnds4", "sha256msg1", "sha256msg2", "sha256rnds2",
        
        # ARM crypto
        "aesd", "aese", "aesimc", "aesmc", "sha1h", "sha1c", "sha1m", "sha1p", "sha1su0", "sha1su1",
        "sha256h", "sha256h2", "sha256su0", "sha256su1",
        
        # Generic crypto terms
        "encrypt", "decrypt", "hash", "digest", "checksum", "signature", "cipher", "key"
    ],
    
    # Memory barrier/synchronization
    "synchronization": [
        # x86/x86-64 sync
        "lock", "mfence", "sfence", "lfence", "xchg", "xadd", "cmpxchg", "cmpxchg8b", "cmpxchg16b",
        
        # ARM sync
        "dmb", "dsb", "isb", "ldrex", "strex", "clrex", "swp",
        
        # MIPS sync
        "sync", "synci", "ll", "sc",
        
        # PowerPC sync
        "sync", "isync", "lwsync", "hwsync", "lwarx", "stwcx",
        
        # RISC-V sync
        "fence", "fence.i", "lr.w", "sc.w", "amoswap.w", "amoswap.d",
        
        # Generic sync
        "barrier", "acquire", "release", "atomic", "transaction", "mutex", "semaphore"
    ],
    
    # Atomic operations
    "atomic": [
        # x86/x86-64 atomic
        "xchg", "xadd", "lock add", "lock sub", "lock inc", "lock dec", "lock and", "lock or",
        "lock xor", "lock cmpxchg", "lock cmpxchg8b", "lock cmpxchg16b",
        
        # ARM atomic
        "ldrex", "strex", "ldaex", "stdex", "swp",
        
        # RISC-V atomic
        "lr.w", "sc.w", "lr.d", "sc.d", "amoadd.w", "amoand.w", "amoor.w", "amoxor.w", "amoswap.w",
        "amoadd.d", "amoand.d", "amoor.d", "amoxor.d", "amoswap.d", "amomin.w", "amomax.w",
        
        # Generic atomic
        "fetch", "compare", "exchange", "swap", "add", "increment", "decrement", "test", "set"
    ],
    
    # 16-bit specific instructions
    "16bit_specific": [
        # x86 16-bit specific
        "pusha", "popa", "pushf", "popf", "cbw", "cwd", "lahf", "sahf", "aam", "aad", "daa", "das", "aas", "aaa",
        "into", "xlat", "arpl", "bound", "enter", "leave", "insb", "insw", "outsb", "outsw",
        
        # Legacy 16-bit support
        "a16", "o16", "data16",
        
        # Z80/8086/6502
        "equ", "lda", "ldx", "stx", "inw", "outw", "pushw", "popw", "ld", "cp",
        
        # Generic 16-bit
        "word", "ptr", "near", "far"
    ],
    
    # 32-bit specific instructions
    "32bit_specific": [
        # x86 32-bit specific
        "pushad", "popad", "pushfd", "popfd", "cwde", "cdq", "bswap",
        "movzx", "movsx", "shld", "shrd", "bsf", "bsr", "bt", "bts", "btr", "btc",
        "cpuid", "rdtsc", "rdmsr", "wrmsr", "sysenter", "sysexit", "invlpg",
        
        # ARM 32-bit
        "ldrd", "strd", "swp", "blx", "cps", "wfi", "wfe", "smc", "ldrex", "strex",
        
        # MIPS 32-bit
        "mfc0", "mtc0", "lwl", "lwr", "swl", "swr",
        
        # PowerPC 32-bit
        "lwz", "stw", "lwbrx", "stwbrx",
        
        # 32-bit addressing
        "eaddr", "dword", "ptr"
    ],
    
    # 64-bit specific instructions
    "64bit_specific": [
        # x86-64 specific
        "movsxd", "cmpxchg16b", "swapgs", "rdtscp", "syscall", "sysret",
        "pushfq", "popfq", "iretq", "stosq", "lodsq", "movsq", "cmpsq", "scasq", "cqo",
        "cdqe", "jrcxz", "movq", "movnti", "prefetch", "crc32", "popcnt", "lzcnt", "tzcnt",
        
        # ARMv8 64-bit (AArch64)
        "ldp", "stp", "ldr", "str", "ldur", "stur", "ldnp", "stnp", "prfm",
        "madd", "msub", "ldar", "stlr", "ldxr", "stxr", "ldaxr", "stlxr",
        
        # MIPS64
        "daddi", "daddiu", "dsll", "dsrl", "dsra", "drotr",
        
        # PowerPC 64-bit
        "ld", "std", "ldx", "stdx", "sldi", "srdi",
        
        # RISC-V 64-bit
        "ld", "sd", "addiw", "slliw", "srliw", "sraiw", "addw", "subw", "sllw", "srlw", "sraw",
        
        # 64-bit addressing
        "qword", "ptr", "rip"
    ]
}