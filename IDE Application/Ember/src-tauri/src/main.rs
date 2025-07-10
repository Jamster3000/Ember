// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::process::Command;
use std::fs;
use std::path::Path;
use tauri_plugin_dialog::DialogExt;
use tauri::Manager;

#[derive(Debug, Serialize, Deserialize)]
struct ProjectFile {
    name: String,
    path: String,
    is_directory: bool,
}

#[derive(Clone, serde::Serialize)]
struct ProcessedText {
    content: String,
    line_count: usize,
    char_count: usize,
    word_count: usize,
}

#[derive(Serialize, Deserialize)]
struct EmberonResult {
    lexer_output: String,
    parser_output: String,
    execution_output: String,
    error: Option<String>,
}

#[tauri::command]
async fn open_file_dialog(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let file_path = app.dialog()
        .file()
        .add_filter("Emberon files", &["emb"])
        .add_filter("All files", &["*"])
        .set_file_name("*.emb")  // Set default pattern
        .blocking_pick_file();
    
    match file_path {
        Some(path) => Ok(Some(path.to_string())),
        None => Ok(None),
    }
}

#[tauri::command]
async fn save_file_dialog(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let file_path = app.dialog()
        .file()
        .add_filter("Emberon files", &["emb"])
        .add_filter("All files", &["*"])
        .set_file_name("untitled.emb")
        .blocking_save_file();
    
    match file_path {
        Some(path) => {
            let mut path_str = path.to_string();
            
            // Check if the file already has an extension
            if !path_str.ends_with(".emb") && !path_str.contains('.') {
                // Add .emb extension if no extension is present
                path_str.push_str(".emb");
            }
            
            Ok(Some(path_str))
        },
        None => Ok(None),
    }
}

#[tauri::command]
async fn read_file(path: String) -> Result<String, String> {
    fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read file: {}", e))
}

#[tauri::command]
async fn write_file(path: String, content: String) -> Result<(), String> {
    fs::write(&path, content)
        .map_err(|e| format!("Failed to write file: {}", e))
}

#[tauri::command]
async fn run_emberon_code(code: String, filename: String, app: tauri::AppHandle) -> Result<EmberonResult, String> {
    // Get the resource path
    let resource_path = app.path_resolver()
        .resolve_resource("compiler")
        .expect("failed to resolve resource");
    
    let compiler_path = resource_path.to_str().unwrap();
    
    println!("Running Emberon code from file: {}", filename);
    
    // Create a temporary file to store the code
    let temp_file = format!("/tmp/{}", filename);
    fs::write(&temp_file, &code)
        .map_err(|e| format!("Failed to write temp file: {}", e))?;
    
    // Run the compiler
    let output = Command::new(compiler_path)
        .arg(&temp_file)  // Pass the temp file as argument
        .output()
        .map_err(|e| format!("Failed to run compiler: {}", e))?;
    
    // Clean up temp file
    let _ = fs::remove_file(&temp_file);
    
    // Parse the output
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    
    // Parse your compiler output
    let (lexer_output, parser_output, execution_output) = parse_compiler_output(&stdout);
    
    let error = if !stderr.is_empty() {
        Some(stderr.to_string())
    } else {
        None
    };
    
    Ok(EmberonResult {
        lexer_output,
        parser_output,
        execution_output,
        error,
    })
}

// Parse your compiler's output format
fn parse_compiler_output(output: &str) -> (String, String, String) {
    let mut lexer_output = String::new();
    let mut parser_output = String::new();
    let mut execution_output = String::new();
    
    let mut current_section = "";
    
    for line in output.lines() {
        if line.starts_with("Lexer output:") {
            current_section = "lexer";
            continue;
        } else if line.starts_with("Parser output:") {
            current_section = "parser";
            continue;
        } else if line.starts_with("OUTPUT:") {
            current_section = "execution";
            execution_output.push_str(&line[7..]); // Remove "OUTPUT:" prefix
            continue;
        }
        
        match current_section {
            "lexer" => {
                lexer_output.push_str(line);
                lexer_output.push('\n');
            }
            "parser" => {
                parser_output.push_str(line);
                parser_output.push('\n');
            }
            "execution" => {
                execution_output.push_str(line);
                execution_output.push('\n');
            }
            _ => {}
        }
    }
    
    (lexer_output, parser_output, execution_output)
}

// NEW: Fast text processing for large files
#[tauri::command]
fn process_large_text(text: String) -> ProcessedText {
    let line_count = text.lines().count();
    let char_count = text.chars().count();
    let word_count = text.split_whitespace().count();
    
    ProcessedText {
        content: text,
        line_count,
        char_count,
        word_count,
    }
}

// NEW: Fast line number generation
#[tauri::command]
fn get_line_numbers(line_count: usize) -> Vec<String> {
    (1..=line_count).map(|i| format!("{:3}", i)).collect()
}

// NEW: Fast cursor position calculation
#[tauri::command]
fn calculate_cursor_position(text: String, cursor_pos: usize) -> (usize, usize) {
    let mut line = 1;
    let mut column = 1;
    
    for (i, ch) in text.char_indices() {
        if i >= cursor_pos {
            break;
        }
        if ch == '\n' {
            line += 1;
            column = 1;
        } else {
            column += 1;
        }
    }
    
    (line, column)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            open_file_dialog,
            save_file_dialog,
            read_file,
            write_file,
            run_emberon_code,
            process_large_text,
            get_line_numbers,
            calculate_cursor_position
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}


//Need to get to use the compiler file to actually run code
//This might mean that the compiler needs an arg to the code file to run