extern token_buffer
extern token_index
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

    MAX_SYMBOLS equ 100 ;maximum number of symbols
    MAX_NAME_LENGTH equ 32 ;maximum length of variable names

section .bss 
    identifier_buffer resb 32
    number_buffer resb 16
    current_char resb 1
    token_start resd 1
    last_token resd 1
    token_length resd 1
    current_pos resd 1
    line_start resd 1

    sym_names resb MAX_SYMBOLS * MAX_NAME_LENGTH ;array of variable names
    sym_values resd MAX_SYMBOLS ;array of variable values
    sym_count resd 1 ;number of symbols

section .text
    global parser

parser:
    push ebp
    mov ebp, esp
    
    ; Initialize symbol table
    call init_symbol_table
    
    ; Reset token index and positions
    xor eax, eax
    mov [token_index], eax
    mov [current_pos], eax
    
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
    cmp eax, 1024  ; Maximum buffer size
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
    mov esp, ebp
    pop ebp
    ret

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
    ; We need to find the most recent identifier token
    ; and extract its name from the buffer
    
    ; Initialize identifier buffer
    mov edi, identifier_buffer
    
    ; Start scanning from line_start position (after skipping leading newlines)
    mov esi, [line_start]
    xor ebx, ebx  ; Track if we've found the identifier

.scan_buffer:
    ; Check if we've reached the end of the buffer
    cmp byte [buffer + esi], 0
    je .done_search
    
    ; Check if current character is a letter (a-z)
    mov al, byte [buffer + esi]
    cmp al, 'a'
    jl .not_letter
    cmp al, 'z'
    jg .not_letter
    
    ; If we're not already in an identifier, start collecting it
    test ebx, ebx
    jnz .collect_char
    
    ; Start of new identifier
    mov ebx, 1
    mov edi, identifier_buffer  ; Reset output buffer
    
.collect_char:
    ; Copy character to identifier buffer
    mov byte [edi], al
    inc edi
    inc esi
    jmp .scan_buffer
    
.not_letter:
    ; If we were in an identifier and hit a delimiter, we're done with this identifier
    test ebx, ebx
    jz .skip_char
    
    ; Check for assignment operator after identifier
    cmp al, '='
    je .found_assignment
    
    ; Otherwise, reset identifier tracking
    mov ebx, 0
    
.skip_char:
    inc esi
    jmp .scan_buffer
    
.found_assignment:
    ; Found "identifier=" pattern, we can stop
    mov byte [edi], 0  ; Null-terminate
    jmp .print_identifier
    
.done_search:
    ; If we didn't find a valid identifier with assignment
    test ebx, ebx
    jz .print_error
    
    ; Null-terminate the identifier
    mov byte [edi], 0
    
.print_identifier:
    ; Print the identifier
    mov eax, 4
    mov ebx, 1
    mov ecx, identifier_buffer
    mov edx, edi
    sub edx, identifier_buffer
    int 0x80
    ret
    
.print_error:
    ; Print question mark for error
    mov byte [identifier_buffer], '?'
    mov byte [identifier_buffer + 1], 0
    
    mov eax, 4
    mov ebx, 1
    mov ecx, identifier_buffer
    mov edx, 1
    int 0x80
    ret
    
.done_id:
    ; Null-terminate the identifier
    mov byte [edi], 0
    
    ; Print the identifier
    mov eax, 4
    mov ebx, 1
    mov ecx, identifier_buffer
    mov edx, edi
    sub edx, identifier_buffer
    int 0x80
    ret

; Extract number value from buffer
print_value:
    ; Initialize number buffer
    mov edi, number_buffer
    
    ; Start searching from line_start position
    mov esi, [line_start]
    
    ; Skip to '=' sign
.find_equals:
    mov al, [buffer + esi]
    cmp al, 0
    je .not_found
    cmp al, '='
    je .found_equals
    inc esi
    jmp .find_equals
    
.found_equals:
    ; Skip '=' and any spaces
    inc esi
.skip_spaces:
    mov al, [buffer + esi]
    cmp al, ' '
    jne .check_digit
    inc esi
    jmp .skip_spaces
    
.check_digit:
    ; Ensure it's a digit
    cmp al, '0'
    jl .not_found
    cmp al, '9'
    jg .not_found
    
.copy_number:
    ; Copy numeric value to buffer
    mov al, [buffer + esi]
    
    ; Check if we reached end of number
    cmp al, ' '
    je .done
    cmp al, 0
    je .done
    cmp al, 10  ; newline
    je .done
    
    ; Ensure it's a digit
    cmp al, '0'
    jl .done
    cmp al, '9'
    jg .done
    
    ; Copy digit to number buffer
    mov [edi], al
    inc esi
    inc edi
    jmp .copy_number
    
.done:
    ; Null-terminate the number
    mov byte [edi], 0
    
    ; Update current_pos to the end of this line
    mov [current_pos], esi
    
    ; If we hit a newline, skip past it
    cmp al, 10
    jne .print_result
    inc dword [current_pos]
    
.print_result:
    ; Print the value
    mov eax, 4
    mov ebx, 1
    mov ecx, number_buffer
    mov edx, edi
    sub edx, number_buffer
    int 0x80
    ret
    
.not_found:
    ; Handle error - didn't find equals sign
    mov byte [edi], '?'
    mov byte [edi + 1], 0
    
    ; Print the error marker
    mov eax, 4
    mov ebx, 1
    mov ecx, number_buffer
    mov edx, 1
    int 0x80
    ret

get_next_token:
    ; Get current token index
    mov eax, [token_index]
    mov ebx, token_buffer

    ; Check if we've reached end of tokens
    cmp eax, 1024  ; Maximum buffer size
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
    
    ; Execute output function with the argument
    call execute_output
    
    ; Expect close parenthesis
    call get_next_token
    cmp al, TOKEN_CLOSE_PAREN
    jne syntax_error
    
    ; Print newline to end function call
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80
    
    jmp parser.parse_loop

; Extract argument value for function call
print_function_arg:
    ; Initialize identifier buffer
    mov edi, identifier_buffer
    
    ; Start from line_start position (after skipping leading newlines)
    mov esi, [line_start]
    
    ; Find "output(" pattern
    ; First find the function name
.find_function:
    mov al, [buffer + esi]
    cmp al, 0
    je .not_found
    
    ; Check for 'o'
    cmp al, 'o'
    jne .next_char
    
    ; Check if it's "output("
    mov ecx, 6  ; Length of "output"
    lea edi, [buffer + esi]
    mov esi, func_output_name
    repe cmpsb
    jne .restore_and_continue
    
    ; We found "output", now check for "("
    mov al, [edi]
    cmp al, '('
    jne .restore_and_continue
    
    ; Found "output(", now extract argument
    inc edi  ; Skip past "("
    mov esi, edi
    mov edi, identifier_buffer
    jmp .skip_spaces
    
.restore_and_continue:
    ; Restore esi to after the current character
    lea esi, [buffer + esi]
    inc esi
    mov edi, identifier_buffer
    jmp .find_function
    
.next_char:
    inc esi
    jmp .find_function
    
.skip_spaces:
    ; Skip spaces after "("
    mov al, [esi]
    cmp al, ' '
    jne .copy_arg
    inc esi
    jmp .skip_spaces
    
.copy_arg:
    ; Copy argument to buffer until ")"
    mov al, [esi]
    
    ; Check if we reached end of argument
    cmp al, ' '
    je .done
    cmp al, ')'
    je .done
    cmp al, 0
    je .done
    cmp al, 10  ; newline
    je .done
    
    ; Copy character to argument buffer
    mov [edi], al
    inc esi
    inc edi
    jmp .copy_arg
    
.done:
    ; Null-terminate the argument
    mov byte [edi], 0
    
    ; Print the argument
    mov eax, 4
    mov ebx, 1
    mov ecx, identifier_buffer
    mov edx, edi
    sub edx, identifier_buffer
    int 0x80
    ret
    
.not_found:
    ; Handle error - didn't find open paren
    mov byte [edi], '?'
    mov byte [edi + 1], 0
    
    ; Print the error marker
    mov eax, 4
    mov ebx, 1
    mov ecx, identifier_buffer
    mov edx, 1
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
    
    ; First check if symbol already exists
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
    mov al, [esi]
    mov bl, [edi]
    cmp al, bl
    jne .no_match
    
    test al, al  ; Check if we reached the end
    jz .match_found
    
    inc esi
    inc edi
    jmp .compare_loop
    
.no_match:
    pop ecx  ; Restore counter
    inc ecx
    jmp .search_loop
    
.match_found:
    pop ecx  ; Restore counter
    
    ; Symbol found at index ecx
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
    
.convert_loop:
    movzx ecx, byte [esi]  ; Get next character
    test ecx, ecx
    jz .done  ; End of string
    
    cmp ecx, '0'
    jl .done  ; Not a digit
    cmp ecx, '9'
    jg .done  ; Not a digit
    
    ; Multiply result by 10
    imul eax, 10
    
    ; Add current digit
    sub ecx, '0'
    add eax, ecx
    
    ; Next character
    inc esi
    jmp .convert_loop
    
.done:
    mov esp, ebp
    pop ebp
    ret

; Convert integer to ASCII string
; Input:
;   - eax: integer to convert
;   - edi: buffer to store result
; Output:
;   - edi: points to end of string (null terminator)
itoa:
    push ebp
    mov ebp, esp
    
    ; Handle negative numbers
    test eax, eax
    jns .positive
    
    ; Negate and add minus sign
    neg eax
    mov byte [edi], '-'
    inc edi
    
.positive:
    ; Save starting position
    push edi
    
    ; Special case for 0
    test eax, eax
    jnz .convert_loop
    
    mov byte [edi], '0'
    inc edi
    jmp .done
    
.convert_loop:
    test eax, eax
    jz .reverse  ; Done when all digits processed
    
    ; Get next digit
    xor edx, edx
    mov ecx, 10
    div ecx  ; eax/10, remainder in edx
    
    ; Convert to ASCII and store
    add dl, '0'
    mov [edi], dl
    inc edi
    
    jmp .convert_loop
    
.reverse:
    ; Null terminate the string
    mov byte [edi], 0
    
    ; Now reverse the digits (stack as temp storage)
    pop esi  ; Start of number
    dec edi  ; Last digit
    
.reverse_loop:
    cmp esi, edi
    jae .reversed
    
    ; Swap bytes
    mov al, [esi]
    mov bl, [edi]
    mov [edi], al
    mov [esi], bl
    
    ; Move inward
    inc esi
    dec edi
    jmp .reverse_loop
    
.reversed:
    ; Find end of string
    mov edi, ebp
    sub edi, 4  ; Offset for saved ebp
    mov edi, [edi]  ; Restore starting address
    
.find_end:
    cmp byte [edi], 0
    je .done
    inc edi
    jmp .find_end
    
.done:
    mov esp, ebp
    pop ebp
    ret

; Execute the output function
execute_output:
    ; Print newline to separate AST output from function output
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80
    
    ; Look up the variable in the symbol table
    call find_symbol
    
    ; Check if variable was found
    cmp eax, -1
    je .undefined_variable
    
    ; Convert value to string for output
    push eax
    
    ; Print "OUTPUT: " message
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_output
    mov edx, 8  ; Length of "OUTPUT: " 
    int 0x80
    
    ; Retrieve the value to print
    pop eax
    
    ; Convert integer to ASCII string in number_buffer
    mov edi, number_buffer
    call itoa
    
    ; Print the value
    mov eax, 4
    mov ebx, 1
    mov ecx, number_buffer
    mov edx, edi
    sub edx, number_buffer
    int 0x80
    
    ; Print newline
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80
    
    ret
    
.undefined_variable:
    ; Print error message
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_undefined
    mov edx, 18  ; Length of "Undefined variable"
    int 0x80
    
    ; Print newline
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80
    
    ret