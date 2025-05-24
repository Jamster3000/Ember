global token_buffer
global token_index
global buffer
extern parser

section .data
    filename db "test.emb", 0
    lexer_banner db "Lexer output:", 10, 0
    parser_banner db 10, "Parser output:", 10, 0
    space db " ", 0
    newline db 10, 0
    
    msg_number db "NUMBER", 0
    msg_identifier db "IDENTIFIER", 0
    msg_assignment db "ASSIGNMENT", 0
    msg_open_paren db "OPEN_PAREN", 0
    msg_close_paren db "CLOSE_PAREN", 0
    msg_function db "FUNCTION", 0
    msg_error db "ERROR", 0
    msg_newline db "NEWLINE", 0

    ; Function name to match
    func_output db "output", 0

section .bss
    token_buffer resb 2048    ; Buffer to store tokens
    token_index  resd 1       ; Index to store position in token buffer
    buffer resb 2048          ; Buffer for file contents

section .text
    global _start

_start:
    ; Open the file 
    mov eax, 5           
    mov ebx, filename    
    mov ecx, 0        
    int 0x80         
    mov ebx, eax       

    ; Read file content into buffer
    mov eax, 3          
    mov ecx, buffer      
    mov edx, 2048      
    int 0x80           
    
    ; Check number of bytes read (in eax)
    test eax, eax
    jz done            

    ; Null-terminate the buffer after the bytes read
    mov byte [buffer + eax], 0

    ; Print lexer banner
    mov eax, 4
    mov ebx, 1
    mov ecx, lexer_banner
    mov edx, 17
    int 0x80

    ; Call lexer to process the buffer
    call lexer

    ; Print parser banner
    mov eax, 4
    mov ebx, 1
    mov ecx, parser_banner
    mov edx, 17
    int 0x80

    call parser

    ; Exit program
    mov eax, 1
    xor ebx, ebx
    int 0x80

lexer: ; Set up initial state for the lexer
    xor esi, esi        ; Buffer index
    xor edi, edi        ; Inside identifier flag

check_token: ; Processes each token character 
    cmp esi, 2048 ; compare current buffer position to 2048
    jge done ; stop lexer if all tokens processed

    xor al, al
    mov al, [buffer + esi]    ; Get character from buffer
    
    ; Check if inside an identifier
    test edi, edi
    jnz inside_identifier

    ; Checks current character with null byte (0) - end of buffer
    cmp al, 0
    je done

    ; if the character is a whitespace, ignore it by jumping to "skip_char"
    cmp al, ' '
    je skip_char

    ; (ASCI 10 = newline) jump to handle_newline if it is a newline
    cmp al, 10
    je handle_newline

    ; Check for negative sign followed by digit
    cmp al, '-'
    je check_negative_number

    ; check for positive digits
    ; less than 0, not a digit
    cmp al, '0'
    jl not_digit
    ; greater than 9, not a digit
    cmp al, '9'
    jg not_digit

    ; process number otherwise
    call process_number
    jmp consume_remaining_digits

check_negative_number: ; Check if the character is a negative sign
    ; Look ahead to see if this is a negative number
    push esi
    inc esi
    
    ; Check if we're still within bounds
    cmp esi, 2048
    jge .not_negative_number
    
    mov al, [buffer + esi]

    ; check if next character is a digit
    cmp al, '0'
    jl .not_negative_number
    cmp al, '9'
    jg .not_negative_number

    ; It's a negative number, restore position and process
    pop esi
    call process_number
    jmp consume_remaining_digits

.not_negative_number: ; If not a negative number, restore position
    ; Not negative number, restore position and continue
    pop esi
    mov al, [buffer + esi] ; Restore current character
    jmp not_digit

consume_remaining_digits: ; Consume remaining digits after negative sign
    inc esi ; Move to next character

.digit_loop: ; Loop to consume all digits after the negative sign
    ;check if still in bounds
    cmp esi, 2048
    jge check_token

    mov al, [buffer + esi]

    ; check if this is still a digit
    cmp al, '0'
    jl check_token
    cmp al, '9'
    jg check_token

    inc esi
    jmp .digit_loop

not_digit: ;process non-digit characters
    ; less than a, not an identifier
    cmp al, 'a'
    jl not_identifier
    ; greater than z, not an identifier
    cmp al, 'z'
    jg not_identifier

    ; if passed both checks, it is an identifier
    mov edi, 1          ; Set inside identifier flag
    call process_identifier
    jmp skip_char ; move to the next character

not_identifier: ; Checks for the "=" character
    cmp al, '='
    jne not_assignment
    call process_assignment ;call this if the character is a "="
    jmp skip_char ; move to the next character

not_assignment: ; detects open parentheses
    cmp al, '('
    jne not_open_paren
    call process_open_paren ;process this if the character is a "("
    jmp skip_char ;move to the next character

not_open_paren: ; detects close parentheses
    cmp al, ')'
    jne not_close_paren
    call process_close_paren ;process this if the character is a ")"
    jmp skip_char ;move to the next character

not_close_paren: ; if character isn't close parentheses, handle the error - they'll be an open "(" without a closed one
    call handle_error
    jmp skip_char ;move to the next character

inside_identifier: ; Checks whether the identifier is finished
    cmp al, ' '
    je end_identifier
    cmp al, '='
    je end_identifier
    cmp al, '('
    je end_identifier
    cmp al, ')'
    je end_identifier
    cmp al, 10 ; newline
    je end_identifier
    cmp al, 0 ; end of buffer (null terminator)
    je end_identifier
    
    ; Continue reading identifier
    jmp skip_char

end_identifier:
    xor edi, edi ; Clear inside identifier flag
    dec esi ; Move back one character to process delimiter
    jmp skip_char ; processed next character

handle_newline:
    ; Ignore newline tokens entirely
    xor edi, edi ; Reset identifier flag on newline
    jmp skip_char ; Skip to the next character

skip_char:
    inc esi ; increases the buffer position index
    jmp check_token ; moves to the next character

process_number: ; Processes a number token
    mov eax, [token_index]             ; Load token index value into eax
    mov byte [token_buffer + eax], 2   ; Token '2' for NUMBER
    inc dword [token_index]            ; Increment token index
    
    ; Print token type
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_number
    mov edx, 6        ; length of string "NUMBER"
    int 0x80
    call print_space ; print space after token
    ret
    
process_identifier: ; Processes an identifier token
    push esi ; Save buffer position
    
    ; Check if this is a function name
    ; this will need updating and changing as more function names are added
    mov edi, func_output
    mov ecx, 6         ; "output" length (currently)
    lea esi, [buffer + esi]
    repe cmpsb ; compare string byte-by-byte with function name
    je .is_function ; jump to .is_function if equal, continue if not
    
    pop esi            ; Restore buffer position
    
    ; Regular identifier
    mov eax, [token_index]             ; Load token index value into eax
    mov byte [token_buffer + eax], 1   ; Token '1' for identifier
    inc dword [token_index]            ; Increment token index
    
    ; Print token type
    push ecx
    push edx ; edx now contains the length of the string
    
    mov ecx, msg_identifier
    call calculate_strlen ; get's the length of the string
    
    ; output length
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_identifier
    int 0x80
    
    ;restores registers and outputs space
    pop edx
    pop ecx
    call print_space
    ret

.is_function: ;called if the identifier is a function
    pop esi ; Restore buffer position
    add esi, 5  ; Move past "output" (6 chars - 1, since we'll increment in skip_char)
    
    ; It's a function
    mov eax, [token_index]             ; Load token index value into eax
    mov byte [token_buffer + eax], 6   ; Token '6' for function
    inc dword [token_index]            ; Increment token index
    
    ; Print token type
    push ecx
    push edx
    
    ; Calculate string length
    mov ecx, msg_function
    call calculate_strlen
    
    ; Print function token
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_function
    int 0x80
    
    pop edx ;restore edx
    pop ecx ;restore ecx
    call print_space ;output space
    ret

process_assignment: ; Processes an assignment token
    mov eax, [token_index]             ; Load token index value into eax
    mov byte [token_buffer + eax], 3   ; Token '3' for assignment
    inc dword [token_index]            ; Increment token index
    
    ; Print token type
    push ecx
    push edx
    
    ; Calculate string length first
    mov ecx, msg_assignment
    call calculate_strlen
    
    ; Now print
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_assignment
    int 0x80
    
    pop edx ;restore edx
    pop ecx ; restore ecx
    call print_space ;output space
    ret

process_open_paren: ; Processes an open parenthesis token
    mov eax, [token_index]             ; Load token index value into eax
    mov byte [token_buffer + eax], 4   ; Token '4' for open parenthesis
    inc dword [token_index]            ; Increment token index
    
    ; Print token type
    push ecx
    push edx
    
    ; Calculate string length first
    mov ecx, msg_open_paren
    call calculate_strlen
    
    ; Now print
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_open_paren
    int 0x80
    
    pop edx
    pop ecx
    call print_space
    ret

process_close_paren: ; Processes a close parenthesis token
    mov eax, [token_index]             ; Load token index value into eax
    mov byte [token_buffer + eax], 5   ; Token '5' for close parenthesis
    inc dword [token_index]            ; Increment token index
    
    ; Print token type
    push ecx
    push edx
    
    ; Calculate string length first
    mov ecx, msg_close_paren
    call calculate_strlen ;edx contains string length
    
    ; Now print
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_close_paren
    int 0x80
    
    pop edx ;restore edx
    pop ecx ;restore ecx

    call print_space ;output space
    ret

handle_error: ;handles any errors or misplaced tokens
    ; Print ERROR token
    mov eax, 4
    mov ebx, 1
    mov ecx, msg_error
    mov edx, 5         ; 'ERROR' is 5 characters
    int 0x80
    call print_space ;output space
    ret

print_space: ;Outputs a space
    mov eax, 4
    mov ebx, 1
    mov ecx, space
    mov edx, 1 ;1 character for a whitespace
    int 0x80
    ret

print_newline: ;Outputs a newline
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1 ;newline is considered 1 character
    int 0x80
    ret

done: ; End of lexer - cleanup
    call print_newline
    ret

calculate_strlen: ; Calculate string length - expects string address in ecx, returns length in edx
    xor edx, edx
.loop: ;Jumps to .done and returns if ecx + edx is null terminator (0) otherwise increment edx by 1 and jumps to .loop again
    cmp byte [ecx + edx], 0
    je .done
    inc edx
    jmp .loop
.done:
    ret
