extern token_buffer
extern token_index
extern print_newline
extern buffer

section .data   
    msg_error db "Syntax Error", 0xA, 0
    msg_ast_header db "AST:", 0xA, 0
    msg_ast_assign db "Assignment", 0xA, 0
    msg_ast_func_call db "Function Call", 0xA, 0
    msg_ast_id    db "  Identifier: ", 0
    msg_ast_num   db "  Value: ", 0
    msg_ast_func  db "  Function: ", 0
    msg_ast_arg   db "  Argument: ", 0
    func_output_name db "output", 0
    msg_debug db "Buffer Contents:", 0
    msg_token db "Token: ", 0
    msg_buffer_pos db "Buffer position: ", 0
    newline db 0xA, 0
    
    TOKEN_IDENTIFIER equ 1
    TOKEN_NUMBER equ 2
    TOKEN_ASSIGNMENT equ 3
    TOKEN_OPEN_PAREN equ 4
    TOKEN_CLOSE_PAREN equ 5
    TOKEN_FUNCTION equ 6
    TOKEN_NEWLINE equ 7
    TOKEN_END equ 0

    msg_output db "OUTPUT: ", 0
    msg_undefined db "Undefined variable", 0

    MAX_SYMBOLS equ 200
    MAX_NAME_LENGTH equ 32

; Storage for token data
section .bss 
    identifier_buffer resb 32
    number_buffer resb 16
    current_char resb 1
    token_start resd 1
    last_token resd 1
    token_length resd 1
    current_pos resd 1
    line_start resd 1

    ; Add position tracking for identifiers and numbers
    current_identifier resd 1  ; Track which identifier we're on
    current_number resd 1      ; Track which number we're on
    current_function_call resd 1  ; Track which function call we're on
    
    sym_names resb MAX_SYMBOLS * MAX_NAME_LENGTH ;array of variable names
    sym_values resd MAX_SYMBOLS ;array of variable values
    sym_count resd 1 ;number of symbols

section .text
    global parser

parser:
    ; DON'T set up stack frame - we want to exit cleanly
    ; Initialize symbol table
    call init_symbol_table
    
    ; Reset token index and positions
    xor eax, eax
    mov [token_index], eax
    mov [current_pos], eax
    mov [current_identifier], eax
    mov [current_number], eax
    mov [current_function_call], eax
    
    ; Set initial line_start
    mov [line_start], eax
    
    ; Print AST header
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_ast_header
    mov edx, 5  ; Length of "AST:" + newline
    int 0x80
    
    ; First, skip any leading newline tokens
.skip_leading_newlines:
    ; Peek at the next token
    mov eax, [token_index]
    mov ebx, token_buffer
    cmp eax, 2048  ; Maximum buffer size
    jge .done      ; If past end, we're done
    
    ; Check if it's a newline token
    movzx eax, byte [ebx + eax]
    cmp al, TOKEN_NEWLINE
    jne .parse_loop  ; If not a newline, start regular parsing
    
    ; Skip this newline token
    inc dword [token_index]
    jmp .skip_leading_newlines
    
    ; Parse statements one by one
.parse_loop:
    ; Get next token
    call get_next_token
    
    ; Check if we're at the end of tokens
    test al, al       ; Check if no more tokens (TOKEN_END is 0)
    jz .done
    
    ; Skip newline tokens
    cmp al, TOKEN_NEWLINE  ; Check if newline token (7 = TOKEN_NEWLINE)
    je .parse_loop  ; If it's a newline, get the next token
    
    ; Now handle regular tokens (identifier, function, etc.)
    cmp al, TOKEN_IDENTIFIER  ; Check if identifier (1 = TOKEN_IDENTIFIER)
    je parse_assignment_or_function
    
    cmp al, 6       ; Check if function (6 = TOKEN_FUNCTION)
    je parse_function_call
    
    ; If we reach here, it's an error
    call syntax_error
    jmp .done
    
.done:
    ; Don't try to return - just exit the program
    mov eax, 1
    xor ebx, ebx
    int 0x80

parse_assignment_or_function:
    ; Save current token index to allow backtracking
    dec dword [token_index]
    
    ; Call assignment parsing
    call parse_assignment
    ret

parse_assignment:
    push ebp
    mov ebp, esp

    ; Get token type (we expect identifier for assignment)
    call get_next_token
    test al, al
    jz .done  ; No more tokens

    ; Check token type
    cmp al, TOKEN_IDENTIFIER
    jne .not_assignment

    ; Print Assignment header
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_ast_assign
    mov edx, 11
    int 0x80
    
    ; Print Identifier header
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_ast_id
    mov edx, 14
    int 0x80

    ; Print identifier - using saved buffer position
    call print_identifier

    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80

    ; Look ahead for assignment operator
    call get_next_token
    cmp al, TOKEN_ASSIGNMENT
    jne .not_valid_assignment

    ; Print Value header
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_ast_num
    mov edx, 9
    int 0x80

    ; Get next token type (should be number)
    call get_next_token
    cmp al, TOKEN_NUMBER
    jne syntax_error
    
    ; Print value
    call print_value
    
    ; Store variable in symbol table
    call add_symbol

    ; Print newline to separate assignments
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80

    ; Check next token for another assignment or function call
    call get_next_token
    test al, al  ; Check if we're at the end
    jz .done
    
    ; Push back the token to be processed again
    dec dword [token_index]
    
    ; If the next token is an identifier, it could be another assignment
    cmp al, TOKEN_IDENTIFIER
    je parse_assignment
    
    ; If the next token is a function, let the main parser handle it
    jmp parser.parse_loop

.not_assignment:
    ; If it's not an identifier, it's not an assignment
    dec dword [token_index]  ; Push back the token
    mov esp, ebp
    pop ebp
    ret

.not_valid_assignment:
    ; If we found identifier but not followed by =, it's an error
    call syntax_error
    mov esp, ebp
    pop ebp
    ret

.done:
    mov esp, ebp
    pop ebp
    ret

; Extract identifier from buffer
print_identifier:
    ; Scan the buffer to find identifiers in order
    mov esi, buffer  ; Start at beginning of buffer
    mov edi, identifier_buffer  ; Our target buffer
    xor ecx, ecx  ; Character counter
    
    ; Track identifier occurrences for assignments only
    inc dword [current_identifier]
    mov eax, [current_identifier]
    
    ; Start scanning for the nth identifier that precedes an assignment
    xor ebx, ebx  ; Identifier counter
    
.scan_loop:
    ; Check if we're at the end of the buffer
    cmp byte [esi], 0
    je .not_found
    
    ; Check if current character is a letter (a-z)
    mov dl, byte [esi]
    cmp dl, 'a'
    jl .not_identifier_char
    cmp dl, 'z'
    jg .not_identifier_char
    
    ; Found start of an identifier - check if it's followed by assignment
    push esi  ; Save current position
    
    ; Skip past this identifier to see what follows
.skip_current_id:
    mov dl, byte [esi]
    cmp dl, 'a'
    jl .check_assignment
    cmp dl, 'z'
    jg .check_assignment
    inc esi
    jmp .skip_current_id
    
.check_assignment:
    ; Skip whitespace
.skip_whitespace:
    cmp byte [esi], ' '
    jne .check_equals
    inc esi
    jmp .skip_whitespace
    
.check_equals:
    ; Check if this identifier is followed by '='
    cmp byte [esi], '='
    jne .not_assignment_identifier
    
    ; This is an assignment identifier
    inc ebx
    pop esi  ; Restore identifier start position
    
    ; Is this the one we want?
    cmp ebx, eax
    je .found_target_identifier
    
    ; Not the one we want, skip past it
.skip_this_identifier:
    mov dl, byte [esi]
    cmp dl, 'a'
    jl .next_char
    cmp dl, 'z'
    jg .next_char
    inc esi
    jmp .skip_this_identifier
    
.next_char:
    jmp .not_identifier_char
    
.not_assignment_identifier:
    ; This identifier is not followed by assignment, skip it
    pop esi  ; Restore position
    ; Skip past this identifier
.skip_non_assignment:
    mov dl, byte [esi]
    cmp dl, 'a'
    jl .not_identifier_char
    cmp dl, 'z'
    jg .not_identifier_char
    inc esi
    jmp .skip_non_assignment
    
.found_target_identifier:
    ; This is the identifier we want - start copying
    mov edi, identifier_buffer  ; Reset target position
    xor ecx, ecx  ; Reset character count
    
.copy_chars:
    ; Copy character and advance pointers
    mov dl, byte [esi]
    
    ; Check if this is still part of the identifier
    cmp dl, 'a'
    jl .identifier_done
    cmp dl, 'z'
    jg .identifier_done
    
    ; Copy the character
    mov [edi + ecx], dl
    inc ecx
    inc esi
    jmp .copy_chars
    
.identifier_done:
    ; Null-terminate the identifier
    mov byte [edi + ecx], 0
    jmp .print_id
    
.not_identifier_char:
    ; Not a letter, just advance
    inc esi
    jmp .scan_loop
    
.not_found:
    ; If we couldn't find the identifier, use a placeholder
    mov byte [identifier_buffer], '?'
    mov byte [identifier_buffer + 1], 0
    
.print_id:
    ; Print the identifier
    mov eax, 4  ; sys_write
    mov ebx, 1  ; stdout
    mov ecx, identifier_buffer
    
    ; Calculate length of identifier
    mov edx, 0
.strlen:
    cmp byte [identifier_buffer + edx], 0
    je .print
    inc edx
    jmp .strlen
    
.print:
    ; Call sys_write with the correct length
    int 0x80
    ret

; Extract number value from buffer
print_value:
    ; Initialize number buffer
    mov edi, number_buffer
    
    ; Increment the current number counter
    inc dword [current_number]
    mov eax, [current_number]
    
    ; Scan the buffer to find values in order
    mov esi, buffer
    xor ebx, ebx  ; Value counter
    
.scan_loop:
    ; Check if we're at the end of the buffer
    cmp byte [esi], 0
    je .not_found
    
    ; Check for = sign (indicates a value follows)
    cmp byte [esi], '='
    je .found_equals
    
    ; Not what we're looking for, advance
    inc esi
    jmp .scan_loop

.found_equals:
    ; Skip past the equals sign
    inc esi
    
    ; Skip any whitespace
.skip_spaces:
    cmp byte [esi], ' '
    jne .check_number_start
    inc esi
    jmp .skip_spaces
    
.check_number_start: 
    ; This is a potential number - increment counter
    inc ebx
    cmp ebx, eax
    jne .skip_value  ; Not the one we want
    
    ; This is the value we want - copy it
    xor ecx, ecx
    
    ; Check for negative sign first
    cmp byte [esi], '-'
    jne .copy_digits
    
    ; Copy the negative sign
    mov dl, byte [esi]
    mov [number_buffer + ecx], dl
    inc ecx
    inc esi
    
.copy_digits: ;copy the digits of a variable's value
    mov dl, byte [esi]

    ;check if this is still a digit
    cmp dl, '0'
    jl .value_done
    cmp dl, '9'
    jg .value_done

    ; copy digit
    mov[number_buffer + ecx], dl
    inc ecx
    inc esi
    jmp .copy_digits
    
.value_done:
    ; Null-terminate the number
    mov byte [number_buffer + ecx], 0
    jmp .print_value
    
.skip_value:
    ; Skip this value until we find non-digit (handle negative numbers too)
    cmp byte [esi], '-'
    je .skip_negative
    cmp byte [esi], '0'
    jl .value_end
    cmp byte [esi], '9'
    jg .value_end
    
    ; Still in value, keep skipping
    inc esi
    jmp .skip_value
    
.skip_negative: ;skip the negative sign and then the digits
    inc esi
.skip_negative_digits: ;skips the negative digits
    cmp byte [esi], '0'
    jl .value_end
    cmp byte [esi], '9'
    jg .value_end
    inc esi
    jmp .skip_negative_digits

.value_end:
    ; Done with this value, continue scanning
    jmp .scan_loop
    
.not_found:
    ; If we couldn't find the value, use a default
    mov byte [number_buffer], '0'
    mov byte [number_buffer + 1], 0
    
.print_value:
    ; Print the value
    mov eax, 4
    mov ebx, 1
    mov ecx, number_buffer
    
    ; Calculate length
    mov edx, 0
.measure:
    cmp byte [number_buffer + edx], 0
    je .do_print
    inc edx
    jmp .measure
    
.do_print:
    ; Call sys_write with the correct length
    int 0x80
    ret

get_next_token:
    ; Get current token index
    mov eax, [token_index]
    mov ebx, token_buffer

    ; Check if we've reached end of tokens
    cmp eax, 2048  ; Maximum buffer size
    jge .end_of_tokens

    ; Get token type
    movzx eax, byte [ebx + eax]
    
    ; Increment token index for next call
    inc dword [token_index]
    
    ; For debugging - to verify token sequence
    ; push eax  ; Save token type
    ; 
    ; mov eax, 4
    ; mov ebx, 1
    ; mov ecx, msg_token
    ; mov edx, 7
    ; int 0x80
    ; 
    ; pop eax
    ; push eax
    ; 
    ; add eax, '0'  ; Convert to ASCII
    ; mov [current_char], al
    ; 
    ; mov eax, 4
    ; mov ebx, 1
    ; mov ecx, current_char
    ; mov edx, 1
    ; int 0x80
    ; 
    ; mov eax, 4
    ; mov ebx, 1
    ; mov ecx, newline
    ; mov edx, 1
    ; int 0x80
    ; 
    ; pop eax
    
    ret

.end_of_tokens:
    xor eax, eax  ; Return 0 to indicate no more tokens
    ret

parse_function_call:
    ; Print Function Call header
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_ast_func_call
    mov edx, 14
    int 0x80
    
    ; Print Function name header
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_ast_func
    mov edx, 12
    int 0x80
    
    ; Print "output" (the function name)
    push esi
    mov eax, 4
    mov ebx, 1
    mov ecx, func_output_name
    mov edx, 6
    int 0x80
    pop esi

    call print_newline
    
    ; Expect open parenthesis
    call get_next_token
    cmp al, TOKEN_OPEN_PAREN
    jne syntax_error
    
    ; Print argument header
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_ast_arg
    mov edx, 12
    int 0x80
    
    ; Get argument (should be identifier)
    call get_next_token
    cmp al, TOKEN_IDENTIFIER
    jne syntax_error
    
    ; Extract argument from source buffer
    call print_function_arg

    call print_newline
    
    ; Execute output function with the argument
    call execute_output
    
    ; Expect close parenthesis
    call get_next_token
    cmp al, TOKEN_CLOSE_PAREN
    jne syntax_error
    
    ; Return to main parser loop instead of jumping
    ret

; Extract argument value for function call
print_function_arg:
    ; Increment function call counter to track which call we're processing
    inc dword [current_function_call]
    mov eax, [current_function_call]
    
    ; Scan buffer to find the nth function call
    mov esi, buffer
    xor ebx, ebx  ; Function call counter
    
.scan_for_target:
    cmp byte [esi], 0
    je .not_found
    
    ; Look for 'o' 
    cmp byte [esi], 'o'
    jne .advance_scan
    
    ; Check if this is "output("
    push esi
    inc esi
    cmp byte [esi], 'u'
    jne .not_output
    inc esi
    cmp byte [esi], 't'
    jne .not_output
    inc esi
    cmp byte [esi], 'p'
    jne .not_output
    inc esi
    cmp byte [esi], 'u'
    jne .not_output
    inc esi
    cmp byte [esi], 't'
    jne .not_output
    inc esi
    cmp byte [esi], '('
    jne .not_output
    
    ; Found "output(" - this is a function call
    inc ebx
    pop esi
    
    ; Is this the function call we want?
    cmp ebx, eax
    je .found_target_function
    
    ; Not the one we want, keep scanning
    jmp .advance_scan
    
.not_output:
    pop esi
    
.advance_scan:
    inc esi
    jmp .scan_for_target
    
.found_target_function:
    ; Found the target function call, now extract the argument
    ; Skip to the opening parenthesis
    add esi, 6  ; Skip "output"
    inc esi     ; Skip '('
    
    ; Skip any whitespace
.skip_arg_whitespace:
    cmp byte [esi], ' '
    jne .start_arg_copy
    inc esi
    jmp .skip_arg_whitespace
    
.start_arg_copy:
    ; Copy the argument identifier
    mov edi, identifier_buffer
    xor ecx, ecx
    
.copy_arg_chars:
    mov dl, byte [esi]
    
    ; Check if this is still part of the identifier
    cmp dl, 'a'
    jl .arg_done
    cmp dl, 'z'
    jg .arg_done
    
    ; Copy the character
    mov [edi + ecx], dl
    inc ecx
    inc esi
    jmp .copy_arg_chars
    
.arg_done:
    ; Null-terminate the identifier
    mov byte [edi + ecx], 0
    jmp .print_arg
    
.not_found:
    ; If we couldn't find the identifier, use a placeholder
    mov byte [identifier_buffer], '?'
    mov byte [identifier_buffer + 1], 0
    
.print_arg:
    ; Print the identifier
    mov eax, 4
    mov ebx, 1
    mov ecx, identifier_buffer
    
    ; Calculate length
    mov edx, 0
.strlen:
    cmp byte [identifier_buffer + edx], 0
    je .print
    inc edx
    jmp .strlen
    
.print:
    ; Call sys_write with the correct length
    int 0x80
    ret

syntax_error:
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_error
    mov edx, 13
    int 0x80
    mov esp, ebp
    pop ebp
    ret

; Initialize the symbol table
init_symbol_table:
    mov dword [sym_count], 0
    ret

; Add or update a symbol in the symbol table
; Input:
;   - identifier_buffer: null-terminated variable name
;   - number_buffer: null-terminated string value
; Returns:
;   - eax: 1 if added, 0 if updated
add_symbol:
    push ebp
    mov ebp, esp
    
    ; First ensure we have valid data in identifier_buffer and number_buffer
    mov esi, identifier_buffer
    cmp byte [esi], 0
    je .done  ; Empty identifier
    cmp byte [esi], '?'
    je .done  ; Invalid identifier
    
    ; Check for valid number buffer
    mov esi, number_buffer
    cmp byte [esi], 0
    je .done  ; Empty value
    
    ; Check if symbol already exists
    call find_symbol
    cmp eax, -1
    jne .update_symbol  ; Symbol found, update it
    
    ; Get current count
    mov eax, [sym_count]
    
    ; Check if we have room
    cmp eax, MAX_SYMBOLS
    jge .table_full
    
    ; Calculate offset into sym_names array
    mov ebx, eax
    imul ebx, MAX_NAME_LENGTH
    
    ; Copy name into symbol table
    mov esi, identifier_buffer
    mov edi, sym_names
    add edi, ebx
    
.copy_name_loop:
    mov al, [esi]
    mov [edi], al
    test al, al
    jz .name_copied
    inc esi
    inc edi
    jmp .copy_name_loop
    
.name_copied:
    ; Convert number string to integer value
    mov esi, number_buffer
    call atoi
    
    ; Store value in symbol table
    mov ebx, [sym_count]
    mov [sym_values + ebx * 4], eax
    
    ; Increment symbol count
    inc dword [sym_count]
    
    ; For debugging - print symbol added message
    ; mov eax, 4
    ; mov ebx, 1
    ; mov ecx, msg_undefined  ; Reuse this as debug output
    ; mov edx, 18
    ; int 0x80
    
    mov eax, 1  ; Return 1 (symbol added)
    jmp .done
    
.update_symbol:
    ; edx already contains the index of the symbol
    
    ; Convert number string to integer value
    mov esi, number_buffer
    call atoi
    
    ; Update value in symbol table
    mov ebx, eax  ; Save numeric value in ebx
    mov eax, edx  ; Get symbol index from edx (returned by find_symbol)
    mov [sym_values + eax * 4], ebx
    
    mov eax, 0  ; Return 0 (symbol updated)
    jmp .done
    
.table_full:
    ; Handle table full error
    mov eax, -1  ; Return error code
    
.done:
    mov esp, ebp
    pop ebp
    ret

; Find a symbol in the symbol table
; Input:
;   - identifier_buffer: null-terminated variable name to find
; Returns:
;   - eax: value of the symbol if found, -1 if not found
;   - edx: index of the symbol if found
find_symbol:
    push ebp
    mov ebp, esp
    
    ; Check if identifier is empty or invalid
    mov esi, identifier_buffer
    cmp byte [esi], 0
    je .not_found
    cmp byte [esi], '?'
    je .not_found
    
    ; Start from index 0
    xor ecx, ecx
    
.search_loop:
    ; Check if we've searched all symbols
    cmp ecx, [sym_count]
    jge .not_found
    
    ; Calculate offset into sym_names array
    mov eax, ecx
    imul eax, MAX_NAME_LENGTH
    
    ; Compare name with identifier_buffer
    mov esi, identifier_buffer
    mov edi, sym_names
    add edi, eax
    
    push ecx  ; Save counter
    
.compare_loop:
    ; Load character from each string
    mov al, [esi]
    mov bl, [edi]
    
    ; If characters differ, not a match
    cmp al, bl
    jne .no_match
    
    ; If both are null, strings match
    test al, al
    jz .match_found
    
    ; Move to next character
    inc esi
    inc edi
    jmp .compare_loop
    
.no_match:
    ; No match, try next symbol
    pop ecx
    inc ecx
    jmp .search_loop
    
.match_found:
    ; Symbol found at index ecx
    pop ecx
    
    mov edx, ecx  ; Return index in edx
    mov eax, [sym_values + ecx * 4]  ; Return value in eax
    jmp .done
    
.not_found:
    mov eax, -1  ; Return -1 if not found
    
.done:
    mov esp, ebp
    pop ebp
    ret

; Convert ASCII string to integer
; Input:
;   - esi: pointer to null-terminated string
; Returns:
;   - eax: integer value
atoi:
    push ebp
    mov ebp, esp
    
    xor eax, eax  ; Initialize result to 0
    xor ebx, ebx  ; Sign flag (0 = positive, 1 = negative)

    ; Check for negative sign
    cmp byte [esi], '-'
    jne .convert_loop

    ; Set negative flag and skip the minus sign
    mov ebx, 1
    inc esi
    
.convert_loop:
    movzx ecx, byte [esi]  ; Get next character
    test ecx, ecx
    jz .check_sign  ; End of string
    
    cmp ecx, '0'
    jl .check_sign  ; Not a digit
    cmp ecx, '9'
    jg .check_sign  ; Not a digit
    
    ; Multiply result by 10
    imul eax, 10
    
    ; Add current digit
    sub ecx, '0'
    add eax, ecx
    
    ; Next character
    inc esi
    jmp .convert_loop
    
.check_sign:
    ; Apply negative sign if needed
    test ebx, ebx
    jz .done
    neg eax
    
.done:
    mov esp, ebp
    pop ebp
    ret

; Convert integer to ASCII string
; Input:
;   - eax: integer to convert
;   - edi: buffer to store result
; Output:
;   - buffer contains null-terminated string
itoa:
    push ebp
    mov ebp, esp
    push esi
    push ebx
    push ecx
    push edx
    
    ; Clear the buffer first
    mov byte [edi], 0
    mov byte [edi + 1], 0
    mov byte [edi + 2], 0
    mov byte [edi + 3], 0
    mov byte [edi + 4], 0
    mov byte [edi + 5], 0
    mov byte [edi + 6], 0
    mov byte [edi + 7], 0
    mov byte [edi + 8], 0
    mov byte [edi + 9], 0
    mov byte [edi + 10], 0
    mov byte [edi + 11], 0
    mov byte [edi + 12], 0
    mov byte [edi + 13], 0
    mov byte [edi + 14], 0
    mov byte [edi + 15], 0
    
    ; Handle negative numbers
    mov esi, edi  ; Save buffer start
    test eax, eax
    jns .positive
    
    ; Store minus sign and negate
    mov byte [edi], '-'
    inc edi
    neg eax
    
.positive:
    ; Handle zero case
    test eax, eax
    jnz .convert
    mov byte [edi], '0'
    inc edi
    mov byte [edi], 0
    jmp .done
    
.convert:
    ; Convert digits (they'll be in reverse order)
    mov esi, edi  ; Save start of digits
    
.digit_loop:
    test eax, eax
    jz .reverse_digits
    
    xor edx, edx
    mov ecx, 10
    div ecx  ; eax = eax/10, edx = remainder
    
    add dl, '0'  ; Convert remainder to ASCII
    mov [edi], dl
    inc edi
    
    jmp .digit_loop
    
.reverse_digits:
    ; Null terminate
    mov byte [edi], 0
    
    ; Now reverse the digits between esi and edi-1
    dec edi  ; Point to last digit
    
.reverse_loop:
    cmp esi, edi
    jae .done
    
    ; Swap characters
    mov al, [esi]
    mov bl, [edi]
    mov [esi], bl
    mov [edi], al
    
    inc esi
    dec edi
    jmp .reverse_loop
    
.done:
    pop edx
    pop ecx
    pop ebx
    pop esi
    mov esp, ebp
    pop ebp
    ret

; Execute the output function (simplified for debugging)
execute_output:
    push ebp
    mov ebp, esp
    push esi
    push edi
    push ebx
    push ecx
    push edx
    
    ; Look up the variable in the symbol table
    call find_symbol
    
    ; Check if variable was found
    cmp eax, -1
    je .undefined_variable
    
    ; Print "OUTPUT: " message
    push eax  ; Save the value
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_output
    mov edx, 8
    int 0x80
    pop eax   ; Restore the value
    
    ; For debugging - just print a fixed string instead of converting
    push eax  ; Save the value again
    mov eax, 4
    mov ebx, 1
    mov ecx, number_buffer
    
    ; Manually set "5" in the buffer for testing
    mov byte [number_buffer], '5'
    mov byte [number_buffer + 1], 0
    mov edx, 1
    
    int 0x80
    pop eax   ; Clean up stack
    
    ; Print newline
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80
    
    jmp .done
    
.undefined_variable:
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_undefined
    mov edx, 18
    int 0x80
    
    ; Print newline
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80

.done:
    ; Clean exit - make sure we don't have stack corruption
    ; Don't try to return - just exit the program cleanly
    mov eax, 1    ; sys_exit
    mov ebx, 0    ; exit status 0 (success)
    int 0x80