from pyvis.network import Network
import re, os, sys
from instruction_categories import INSTRUCTION_CATEGORIES

LABEL_PATTERN = re.compile(r'^\s*([A-Za-z0-9_.$@]+):\s*(?:;.*)?$')
INSTRUCTION_PATTERN = re.compile(r'^\s*([A-Za-z0-9.]+)\s+')
JUMP_PATTERN = re.compile(r'\b(?:j|jmp|jp|jr|b|br|bra)\s+([A-Za-z0-9_.$@]+)', re.IGNORECASE)
CALL_PATTERN = re.compile(r'\b(?:call|bl|bsr|jsr)\s+([A-Za-z0-9_.$@]+)', re.IGNORECASE)
RETURN_PATTERN = re.compile(r'\b(?:ret|rts|rtn|retn|return|bx\s+lr)\b', re.IGNORECASE)
GLOBAL_PATTERN = re.compile(r'^\s*(?:global|globl|export|public)\s+(.+)$', re.IGNORECASE)
EXTERN_PATTERN = re.compile(r'^\s*(?:extern|extrn|import|external)\s+(.+)$', re.IGNORECASE)
SECTION_PATTERN = re.compile(r'^\s*(?:section|segment|cseg|dseg)\s+([^\s;]+)', re.IGNORECASE)

def parse_assembly_code(file_paths=None):
    """
    Parses the assmebly code and creates the flowchart.
    
    Args:
        file_paths (list) : List of file paths to parse. If None, it will use the current directory.

    Returns:
        net (Network) : The pyvis network object containing the flowchart.
    """ 

    if file_paths is None:
        file_paths = []
    elif isinstance(file_paths, str):
        file_paths = [file_paths]

    net = Network(height="750px", width="100%", notebook=True, directed=True)

    all_labels = {}
    externals = {}
    globals_dict = {}
    
    file_id = 0
    for file_path in file_paths:
        file_id += 1
        file_name = os.path.basename(file_path)

        file_comments = extract_comments(file_path)
        current_label = None

        with open(file_path, 'r') as file:
            assembly_code = file.read()

        labels = {}
        current_label = None
        current_section = None

        externals[file_name] = []
        globals_dict[file_name] = []

        for line in assembly_code.split('\n'):
            line = line.strip()
            if not line:
                continue

            comment = ""
            if ';' in line:
                parts = line.split(';', 1)
                line = parts[0].strip()
                comment = parts[1].strip()
                if not line:
                    continue

            if line.startswith('section'):
                current_section = line.split()[1]
                continue

            if line.startswith('extern'):
                extern_symbols = line[6:].strip().split(',')
                externals[file_name].extend([s.strip() for s in extern_symbols])
                continue

            if line.startswith('global'):
                global_symbols = line[6:].strip().split(',')
                globals_dict[file_name].extend([s.strip() for s in global_symbols])
                continue

            if line.endswith(':'):
                label = line[:-1].strip()
                parent_label = None

                if label.startswith('.'):
                    if current_label and ":" in current_label:
                        parent_full = current_label.split(":", 1)[1]
                        parent_base = parent_full.split(".")[0] if "." in parent_full else parent_full
                        parent_label = f"{file_name}:{parent_base}"
                        current_label = f"{file_name}:{parent_base}{label}"
                    else:
                        current_label = f"{file_name}:{label}"
                else:
                    current_label = f"{file_name}:{label}"

                labels[current_label] = {
                    "instructions": [],
                    "comments": [],
                    "file": file_name,
                    "raw_label": label,
                    "section": current_section,
                    "parent": parent_label,
                    "is_local": label.startswith('.')
                }
                
                # Add any comments that were attached to the label in the comments dictionary
                if label in file_comments and file_comments[label]:
                    labels[current_label]["comments"].extend(file_comments[label])
            elif current_label and line:
                labels[current_label]["instructions"].append(line)
                if comment:
                    labels[current_label]["comments"].append(comment)

        all_labels.update(labels)
    
    for label, data in all_labels.items():
        purpose = determine_purpose(data["raw_label"], data["instructions"], data["comments"])

        label_comments = data["comments"]
        description, full_description = get_comment_description(label_comments)

        if description:
            display_label = f"{data['raw_label']}\n({purpose})\n\"{description}\"\n[{data['file']}]"
        else:
            display_label = f"{data['raw_label']}\n({purpose})\n[{data['file']}]"

        tooltip = f"{data['raw_label']} - {purpose}\n\n"
        tooltip += f"File: {data['file']}\n"

        if data['section']:
            tooltip += f"Section: {data['section']}\n"

        if description:
            tooltip += f"Description: {full_description}\n"

        if data.get("is_local", False):
            if data.get("parent"):
                parent_label = data["parent"].split(":", 1)[1] if ":" in data["parent"] else data["parent"]
                tooltip += f"Local label under: {parent_label}\n"
            else:
                tooltip += "Local label\n"
        
        instruction_text = " ".join([i.lower() for i in data["instructions"]])
        if "ret" in instruction_text:
            tooltip += "Returns control to caller\n"
        elif "jmp" in instruction_text:
            tooltip += "Unconditional Jump\n"
        elif any(j in instruction_text for j in ["je ", "jne ", "jg ", "jll ", "jge ", "jle "]):
            tooltip += "Conditional branch\n"

        tooltip += "\n"

        for i, instr in enumerate(data["instructions"]):
            comment = data["comments"][i] if i < len(data["comments"]) and data["comments"][i] else ""
            tooltip += f"{instr}\n"

        node_style = get_node_color(data["raw_label"], purpose, data["file"])
        net.add_node(
            label, 
            label=display_label, 
            title=tooltip, 
            color=node_style["color"],
            borderWidth=node_style["border"]["width"],
            borderWidthSelected=4,
            font={
                "background": "#ffffff90",
                "strokeWidth": 3,
                "strokeColor": "white",
                "size": 14
            },
            shapeProperties={"borderDashes": node_style["border"].get("dash", False)}
        )

    for label, data in all_labels.items():
        if data.get("parent"):
            net.add_edge(data["parent"], label, color='#00AA00', title="Contains")

    for label, data in all_labels.items():
        file_name = data["file"]

        for instr in data["instructions"]:
            if re.search(r'\bjmp\s+(\w+)', instr, re.IGNORECASE):
                target_raw = re.search(r'\bjmp\s+(\w+)', instr, re.IGNORECASE).group(1)
                target = f"{file_name}:{target_raw}"
                if target in all_labels:
                    net.add_edge(label, target, color='red', title="Jump to")

            elif re.search(r'\bj[a-z]+\s+(\w+)', instr, re.IGNORECASE):
                target_raw = re.search(r'\bj[a-z]+\s+(\w+)', instr, re.IGNORECASE).group(1)
                target = f"{file_name}:{target_raw}"
                if target in all_labels:
                    net.add_edge(label, target, color='orange', title='Conditional')

            elif re.search(r'\bcall\s+(\w+)', instr, re.IGNORECASE):
                target_raw = re.search(r'\bcall\s+(\w+)', instr, re.IGNORECASE).group(1)
                
                if target_raw in externals[file_name]:
                    for other_file, globals_list in globals_dict.items():
                        if target_raw in globals_list:
                            target = f"{other_file}:{target_raw}"
                            if target in all_labels:
                                net.add_edge(label, target, color='#AAAAAA', style='dashed', title=f'External Call ({other_file})')
                else:
                    target = f"{file_name}:{target_raw}"
                    if target in all_labels:
                        net.add_edge(label, target, color='blue', title='Call')

        has_unconditional_jump = any(re.search(r'\bjmp\s+\w+', instr, re.IGNORECASE) for instr in data["instructions"])
        has_return = any(re.search(r'\bret\b', instr, re.IGNORECASE) for instr in data["instructions"])

        if not has_unconditional_jump and not has_return:
            file_labels = [l for l in all_labels.keys() if l.startswith(f"{file_name}:")]
            try:
                current_index = file_labels.index(label)
                if current_index < len(file_labels) - 1:
                    next_label = file_labels[current_index + 1]
                    net.add_edge(label, next_label, color="green", title="Next")
            except ValueError:
                pass

    for file_name, extern_list in externals.items():
        for extern_symbol in extern_list:
            for other_file, global_list in globals_dict.items():
                for label, data in all_labels.items():
                    if data["file"] == file_name:
                        for instr in data["instructions"]:
                            if extern_symbol in instr:
                                for other_label, other_data in all_labels.items():
                                    if other_data["file"] == other_file and other_data["raw_label"] == extern_symbol:
                                        net.add_edge(label, other_label, color="#AAAAAA", title=f'Uses {extern_symbol}', style='dashed')
                                        break

    #find the optimal layout
    #There is issues with linear flowcharts and non-linear multi-level ones.
    nodes = list(all_labels.keys())
    edges_count = len(net.get_edges())

    #number of levels in hierarchy
    levels = {}
    for label in nodes:
        paths_to_node = 0
        for other in nodes:
            if other != label:
                for instr in all_labels[other]["instructions"]:
                    if all_labels[label]["raw_label"] in instr:
                        paths_to_node += 1
        levels[label] = paths_to_node

    max_level = max(levels.values()) if levels else 0
    avg_connections = edges_count / len(nodes) if nodes else 0

    # Graph complexity detection - simplified
    edges = net.get_edges()
    node_connections = {}

    # Calculate in/out connections for each node
    for edge in edges:
        from_node = edge["from"]
        to_node = edge["to"]

        if from_node not in node_connections:
            node_connections[from_node] = {"in": 0, "out": 0}
        if to_node not in node_connections:
            node_connections[to_node] = {"in": 0, "out": 0}

        node_connections[from_node]["out"] += 1
        node_connections[to_node]["in"] += 1

    # Count nodes with simple linear structure (max 1 input, max 1 output)
    linear_nodes = 0
    total_nodes = len(nodes)
    for node, connections in node_connections.items():
        if connections["in"] <= 1 and connections["out"] <= 1:
            linear_nodes += 1

    # Determine graph complexity
    is_mostly_linear = (linear_nodes / total_nodes) >= 0.75 if total_nodes > 0 else False
    is_mostly_same_level = max_level <= 2

    # Special case for long assembly functions with many nested blocks
    # but still fundamentally linear in execution
    if max_level >= 30 and total_nodes >= 20 and total_nodes <= 60:
        is_linear = True
    else:
        is_linear = is_mostly_linear or is_mostly_same_level

    if is_linear:
        net.set_options("""
            {
                "physics": {
                    "enabled": true,
                    "hierarchicalRepulsion": {
                        "nodeDistance": 550,
                        "centralGravity": 0.01,
                        "springLength": 500,
                        "springConstant": 0.01,
                        "avoidOverlap": 1.0
                    }
                },
                "layout": {
                    "hierarchical": {
                        "enabled": true,
                        "direction": "UD",
                        "sortMethod": "directed",
                        "levelSeparation": 250,
                        "nodeSpacing": 700,
                        "treeSpacing": 300,
                        "blockShifting": true,
                        "edgeMinimization": true
                    }
                },
                "edges": {
                    "smooth": {
                        "type": "vertical",
                        "forceDirection": "vertical",
                        "roundness": 0.2
                    },
                    "arrows": {
                        "to": {
                            "enabled": true,
                            "scaleFactor": 0.7
                        }
                    },
                    "font": {
                        "background": "white",
                        "strokeWidth": 3,
                        "strokeColor": "white"
                    },
                    "width": 1.5,
                    "selectionWidth": 3
                },
                "nodes": {
                    "font": {
                        "background": "white",
                        "strokeWidth": 4,
                        "strokeColor": "white",
                        "size": 14
                    },
                    "margin": 12,
                    "borderWidth": 2,
                    "shadow": {
                        "enabled": true,
                        "size": 4,
                        "x": 2,
                        "y": 2,
                        "color": "rgba(0,0,0,0.2)"
                    }
                },
                "interaction": {
                    "zoomView": true,
                    "dragView": true,
                    "hover": true,
                    "navigationButtons": true
                }
            }
            """)
    else:
        print("complex")
        #complex layout
        net.set_options("""
        {
            "physics": {
                "enabled": true,
                "hierarchicalRepulsion": {
                    "nodeDistance": 350,
                    "centralGravity": 0.005, 
                    "springLength": 350,
                    "springConstant": 0.005, 
                    "avoidOverlap": 1.0
                },
                "stabilization": {
                    "iterations": 2000
                }
            },
            "layout": {
                "hierarchical": {
                    "enabled": true,
                    "direction": "UD",
                    "sortMethod": "directed",
                    "levelSeparation": 450,  
                    "nodeSpacing": 400,      
                    "treeSpacing": 500,   
                    "blockShifting": false, 
                    "edgeMinimization": false
                }
            },
            "edges": {
                "smooth": {
                    "enabled": true,
                    "type": "straightCross",  
                    "roundness": 0         
                },
                "arrows": {
                    "to": {
                        "enabled": true,
                        "scaleFactor": 0.7
                    }
                },
                "color": {
                    "inherit": "from",       
                    "opacity": 0.7         
                },
                "width": 1.0,              
                "selectionWidth": 2,
                "hoverWidth": 1.5
            },
            "nodes": {
                "shape": "box",
                "margin": 10,
                "widthConstraint": {
                    "maximum": 250      
                },
                "font": {
                    "size": 14,
                    "face": "arial",
                    "background": "white",
                    "strokeWidth": 3,
                    "strokeColor": "white"
                },
                "shadow": {
                    "enabled": true,
                    "size": 3,
                    "x": 2,
                    "y": 2
                }
            },
            "interaction": {
                "hover": true,
                "multiselect": true,
                "keyboard": {
                    "enabled": true
                },
                "navigationButtons": true
            }
        }
        """)

    return net

def extract_comments(asm_file):
    """
    Extracts comments from an assembly file.
    
    Args:
        asm_file (str) : The path to the assembly file.

    Returns:
        list: A list of comments extracted from the file.
    """

    comments = {}
    current_label = None
    pre_label_comments = []

    inline_comment_pattern = re.compile(r';(.*)$|//(.*)$|#(.*)$')
    label_pattern = re.compile(r'^([a-zA-Z0-9_.$]+):')

    with open(asm_file, 'r') as f:
        lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()

            #skip empty lines
            if not line:
                continue

            comment_match = inline_comment_pattern.search(line)
            comment_text = None
            if comment_match:
                #get group matched 
                comment_text = comment_match.group(1) or comment_match.group(2) or comment_match.group(3)
                if comment_text is not None:
                    comment_text = comment_text.strip()

            label_match = label_pattern.match(line)

            if label_match:
                #found new label
                label_name = label_match.group(1)
                current_label = label_name

                if current_label not in comments:
                    comments[current_label] = []

                #accumulated pre-label comments
                if pre_label_comments:
                    comments[current_label].extend(pre_label_comments)
                    pre_label_comments = []

                #inline comment on the label line
                if comment_text:
                    comments[current_label].append(comment_text)
            elif comment_text:
                if current_label:
                    comments[current_label].append(comment_text)
                else:
                    pre_label_comments.append(comment_text)
    return comments

def get_comment_description(comments):
    """
    Extracts a meaningful description from comments.
    
    Args:
        comments (list) : List of comments associated with the label.

    Returns:
        str: A meaningful description extracted from the comments.
    """

    if not comments:
        return "", ""
    
    #join non-empty comments
    all_comments = " ".join([c.strip().lstrip(';').lstrip('/').lstrip('#').strip() for c in comments if c])

    if not all_comments:
        return "", ""
    
    for comment in comments:
        cleaned = comment.strip().lstrip(';').lstrip('/').lstrip('#').strip()
        if cleaned and len(cleaned) >= 3:
            if len(cleaned) > 17:
                cleaned_updated = cleaned[:14] + "..."
                return cleaned_updated, cleaned
            return cleaned, cleaned

    return "", ""

def determine_purpose(label, instructions, comments):
    """
    Determines the purpose of a label based on its instructions and content
    
    Args:
        label (str) : The label to determine the purpose of.
        instructions (list) : The instructions associated with the label.
        comments (list) : The comments associated with the label.

    Returns:
        str: The purpose of the label.
    """

    # Handle various entry point naming conventions across architectures
    entry_point_labels = ["_start", "main", "start", "entry", "_main", "__start", "__main"]
    if label.lower() in entry_point_labels or "_start" in label.lower():
        return "Entry Point"

    #exit/program finished detection
    exit_indicators = ["exit", "quit", "terminate", "end", "_exit", "done"]
    
    if any(exit_word in label.lower() for exit_word in exit_indicators) and not label.startswith('.'):
        return "Exit Point"

    instr_text = " ".join([i.lower() for i in instructions])
    comment_text = " ".join([c.lower() for c in comments if c]).lower()

    #termination indicators in comments
    if any(hint in comment_text for hint in ["program exit", "exit program", "end of program", "return to os"]):
        return "Exit Point"
        
    #typical exit syscalls or return patterns
    if RETURN_PATTERN.search(instr_text) and (
        # Return in main is usually program exit 
        label.lower() == "main" or 
        # The following are common exit patterns
        "exit" in instr_text or
        "sys_exit" in instr_text or
        "int 0x80" in instr_text and ("eax, 1" in instr_text or "rax, 60" in instr_text) or
        ("syscall" in instr_text and "rax, 60" in instr_text)
    ):
        return "Exit Point"

    # Special purpose detection based on comments
    if any(hint in comment_text for hint in ["initialize", "setup", "init"]):
        return "Initialization"
    if any(hint in comment_text for hint in ["cleanup", "destroy", "free"]):
        return "Cleanup"
    
    # Section headers detection
    if "section" in label.lower():
        if "data" in label.lower():
            return "Data Section"
        elif "bss" in label.lower():
            return "BSS Section"
        elif "text" in label.lower() or "code" in label.lower():
            return "Code Section"
        return "Section Header"
    
    # Function detection based on return instructions
    if RETURN_PATTERN.search(instr_text):
        function_types = {
            "print": "Print Function",
            "draw": "Graphics Function",
            "read": "Input Function",
            "write": "Output Function",
            "get": "Getter Function",
            "set": "Setter Function",
            "calc": "Calculation Function",
            "parse": "Parsing Function",
            "lex": "Lexical Function",
            "exec": "Execution Function",
            "init": "Initialization Function",
            "alloc": "Memory Allocation",
            "free": "Memory Deallocation",
            "sort": "Sorting Function",
            "search": "Search Function",
            "convert": "Conversion Function",
            "handle": "Handler Function",
            "process": "Processing Function"
        }

        for pattern, purpose in function_types.items():
            if pattern in label.lower() or any(pattern in c.lower() for c in comments if c):
                return purpose
        return "Function"

    # Local label patterns (usually starting with .)
    if label.startswith('.'):
        local_patterns = {
            "loop": "Loop",
            "next": "Next Item Processing",
            "start": "Start Point",
            "end": "End Block",
            "done": "Completion Point",
            "exit": "Block Exit",
            "error": "Error Handler",
            "fail": "Failure Handler",
            "success": "Success Handler",
            "check": "Validation Check",
            "skip": "Skip Section",
            "retry": "Retry Logic",
            "compare": "Comparison Block",
            "cmp": "Comparison Block"
        }

        for pattern, purpose in local_patterns.items():
            if pattern in label.lower():
                return purpose
    
    # Loop detection based on naming or content
    if "loop" in label.lower() or "loop" in comment_text:
        return "Loop"
    
    # SIMD/Vector operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["simd"]):
        return "SIMD Operation"
        
    # Bitwise operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["bitwise"]):
        return "Bitwise Operation"
        
    # Floating-point operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["floating_point"]):
        return "Floating-Point Operation"
    
    # Jump/Branch operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["jump"]):
        return "Control Flow"
    
    # Function call operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["call"]):
        return "Function Call"
    
    # Comparison operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["comparison"]):
        return "Comparison"
        
    # Data transfer operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["data_transfer"]):
        return "Data Transfer"
        
    # Arithmetic operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["arithmetic"]):
        return "Arithmetic"
        
    # System operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["system"]):
        return "System Operation"
        
    # String operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["string"]):
        return "String Operation"
        
    # Cryptographic operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["crypto"]):
        return "Cryptographic Operation"
        
    # Synchronization operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["synchronization"]):
        return "Synchronization"
        
    # Atomic operations
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["atomic"]):
        return "Atomic Operation"
        
    # 16-bit specific instructions
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["16bit_specific"]):
        return "16-bit Code"
        
    # 32-bit specific instructions
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["32bit_specific"]):
        return "32-bit Code"
        
    # 64-bit specific instructions
    if any(instr in instr_text for instr in INSTRUCTION_CATEGORIES["64bit_specific"]):
        return "64-bit Code"
    
    # Default fallback
    return "Code Block"

def analyze_cross_file_dependencies(all_files):
    """
    Analyzes relationships between assembly files.
    
    Args:
        all_files (list) : paths to all assembly files.

    Returns:
        dict: Dictionary of file dependencies.
    """

    dependencies = {}

    #collect all global symbols
    global_symbols = {}
    for file_path in all_files:
        file_name = os.path.basename(file_path)
        dependencies[file_name] = {
            "includes": set(),
            "uses": set(),
            "provides": set()
        }

        try:
            with open(file_path, 'r') as file:
                content = file.read()

            for match in GLOBAL_PATTERN.finditer(content):
                for symbol in match.group(1).split(','):
                    symbol = symbol.strip()
                    global_symbols[symbol] = file_name
                    dependencies[file_name]["provides"].add(symbol)

        except Exception as e:
            print(f"Erroranalyzing globals in {file_path}: {e}")

    for file_path in all_files:
        file_name = os.path.basename(file_path)

        #find include relationships
        includes = find_included_files(file_path)
        dependencies[file_name]["includes"].update([os.path.basename(inc) for inc in includes])

        #find external symbol usage
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            for match in EXTERN_PATTERN.finditer(content):
                for symbol in match.group(1).split(','):
                    symbol = symbol.strip()
                    if symbol in global_symbols and global_symbols[symbol]:
                        dependencies[file_name]["uses"].add(symbol)
        except Exception as e:
            print(f"Error analyzing exerns in {file_path}: {e}")

    return dependencies

def find_included_files(file_path, base_dir="."):
    included_files = []
    include_pattern = re.compile(r'^\s*(?:include|%include|\.include)\s+[\'"]?([^\'";]+)[\'"]?', re.IGNORECASE)

    try:
        with open(file_path, 'r') as f:
            for line in f:
                match = include_pattern.search(line)
                if match:
                    include_path = match.group(1)
                    if not os.path.isabs(include_path):
                        include_path = os.path.join(base_dir, include_path)

                    if os.path.exists(include_path):
                        included_files.append(include_path)
                        nested_includes = find_included_files(include_path, os.path.dirname(include_path))
                        included_files.extend(nested_includes)
    except Exception as e:
        print(f"Error processing includes in {file_path}: {e}")

    return included_files

def get_node_color(label, purpose, file_name):
    """
    Get color for node based on it's purpose and file
    
    args:
        label (str) : The label to determine the color of.
        purpose (str) : The purpose of the label.
        file_name (str) : The name of the file the label is in.

    Returns:
        dict: Node style configuration.
    """

    #colour by purpose (same as before)
    if "Entry Point" in purpose:
        color = "green"
    elif "Exit Point" in purpose:
        color = "red"
    elif "Function" in purpose:
        color = "lightblue"
    elif "Loop" in purpose:
        color = "purple"
    elif "Block Exit" in purpose or "End Block" in purpose:
        color = "#ffaa66" 
    elif "Data" in purpose or "Operation" in purpose:
        color = "orange"
    elif "Comparison" in purpose:
        color = "yellow"
    elif "Error" in purpose or "Undefined" in purpose:
        color = "#ff9966" 
    elif "Success" in purpose or "Completion" in purpose:
        color = "#66cc99" 
    elif "Control Flow" in purpose:
        color = "#3333cc" 
    else:
        color = "#dddddd"

    # Enhanced node style with background for text readability
    return {
        "color": color,
        "border": {
            "width": 2,
            "color": "#000000"
        },
        "background": "#ffffff",  # Add white background for labels
        "font": {
            "background": "#ffffff",  # Text with white background
            "strokeWidth": 3,        # Text outline
            "strokeColor": "#ffffff"  # White outline around text
        }
    }

def add_fixed_legend(html_file):
    """
    Adds a fixed legend to the flowchart HTML file.
    
    args:
        html_file (str) : The path to the HTML file to modify.

    Returns:
        None
    """

    with open(html_file, 'r') as file:
        content = file.read()

    legend_html = """
    <div id="fixed-legend" style="
        position: fixed;
        top: 5px;
        right: 10px;
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 10px;
        z-index: 1000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        max-height: 100vh;
        overflow-y: auto;
        width: 280px;
    ">
        <div style="font-weight: bold; margin-bottom: 10px;">SEARCH</div>
        <!-- Search controls remain unchanged -->
        <div style="margin-bottom: 15px;">
            <input type="text" id="node-search" placeholder="Search nodes..." style="width: 100%; padding: 5px; border: 1px solid #ccc; border-radius: 3px; margin-bottom: 5px;">
            <div>
                <select id="search-type" style="width: 100%; padding: 5px; border: 1px solid #ccc; border-radius: 3px;">
                    <option value="label">Label</option>
                    <option value="purpose">Purpose</option>
                    <option value="file">File</option>
                    <option value="all">All Fields</option>
                </select>
            </div>
            <div style="margin-top: 5px;">
                <button onclick="searchNodes()" style="padding: 5px 10px; background-color: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer; margin-right: 5px;">Search</button>
                <button onclick="resetSearch()" style="padding: 5px 10px; background-color: #f44336; color: white; border: none; border-radius: 3px; cursor: pointer;">Reset</button>
            </div>
            <div id="search-results" style="margin-top: 10px; max-height: 150px; overflow-y: auto; display: none;">
                <div style="font-weight: bold; margin-bottom: 5px;">Results:</div>
                <ul id="results-list" style="padding-left: 20px; margin: 0;"></ul>
            </div>
        </div>
        <hr style="margin: 8px 0;">
        <div style="font-weight: bold; margin-bottom: 10px;">NODE TYPES</div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="The starting point of program execution (e.g., _start, main)">
            <div style="width: 15px; height: 15px; background-color: green; margin-right: 10px;"></div>
            <div>Entry Point</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="The starting point of program execution (e.g., _start, main)">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="The final termination point where the program exits completely">
            <div style="width: 15px; height: 15px; background-color: red; margin-right: 10px;"></div>
            <div>Exit Point</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="The final termination point where the program exits completely">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Marks the end of a logical block but not program termination">
            <div style="width: 15px; height: 15px; background-color: #ffaa66; margin-right: 10px;"></div>
            <div>Block End/Exit</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Marks the end of a logical block but not program termination">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="A reusable code block that can be called from multiple locations">
            <div style="width: 15px; height: 15px; background-color: lightblue; margin-right: 10px;"></div>
            <div>Function</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="A reusable code block that can be called from multiple locations">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Code that repeats execution multiple times (for/while/repeat)">
            <div style="width: 15px; height: 15px; background-color: purple; margin-right: 10px;"></div>
            <div>Loop</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Code that repeats execution multiple times (for/while/repeat)">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Blocks focused on data manipulation and operations">
            <div style="width: 15px; height: 15px; background-color: orange; margin-right: 10px;"></div>
            <div>Data Operation</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Blocks focused on data manipulation and operations">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Code that compares values and makes decisions">
            <div style="width: 15px; height: 15px; background-color: yellow; margin-right: 10px;"></div>
            <div>Comparison</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Code that compares values and makes decisions">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Code that handles error conditions and exceptions">
            <div style="width: 15px; height: 15px; background-color: #ff9966; margin-right: 10px;"></div>
            <div>Error Handling</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Code that handles error conditions and exceptions">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Code that signals successful completion of operations">
            <div style="width: 15px; height: 15px; background-color: #66cc99; margin-right: 10px;"></div>
            <div>Success/Completion</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Code that signals successful completion of operations">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Code that manages program flow and execution order">
            <div style="width: 15px; height: 15px; background-color: #3333cc; margin-right: 10px;"></div>
            <div>Control Flow</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Code that manages program flow and execution order">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Generic code blocks with no specific categorization">
            <div style="width: 15px; height: 15px; background-color: #dddddd; margin-right: 10px;"></div>
            <div>Other Code Block</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Generic code blocks with no specific categorization">ⓘ</div>
        </div>
        <hr style="margin: 8px 0;">
        <div style="font-weight: bold; margin-bottom: 10px;">CONNECTION TYPES</div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Unconditional transfer of control to another location">
            <div style="width: 30px; height: 3px; background-color: red; margin-right: 10px;"></div>
            <div>Jump</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Unconditional transfer of control to another location">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Transfer of control that depends on a condition being met">
            <div style="width: 30px; height: 3px; background-color: orange; margin-right: 10px;"></div>
            <div>Conditional Jump</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Transfer of control that depends on a condition being met">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Normal sequential execution to the next instruction">
            <div style="width: 30px; height: 3px; background-color: green; margin-right: 10px;"></div>
            <div>Next Instruction</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Normal sequential execution to the next instruction">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Hierarchical relationship showing one block is part of another">
            <div style="width: 30px; height: 3px; background-color: #00AA00; margin-right: 10px;"></div>
            <div>Contains (Parent-Child)</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Hierarchical relationship showing one block is part of another">ⓘ</div>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;" title="Connection to code in another source file">
            <div style="width: 30px; height: 3px; background-color: #AAAAAA; border-top: 1px dashed #444444; margin-right: 10px;"></div>
            <div>External Reference</div>
            <div style="margin-left: auto; font-size: 16px; cursor: help;" title="Connection to code in another source file">ⓘ</div>
        </div>
    </div>

    <script>
        // Search function code remains unchanged
        function searchNodes() {
            const searchTerm = document.getElementById('node-search').value.toLowerCase();
            const searchType = document.getElementById('search-type').value;
            const resultsList = document.getElementById('results-list');
            const searchResultsDiv = document.getElementById('search-results');
            
            // Clear previous results
            resultsList.innerHTML = '';
            
            if (!searchTerm) {
                searchResultsDiv.style.display = 'none';
                return;
            }

            // Get all nodes
            const nodes = network.body.data.nodes.get();
            const matches = [];

            // Filter nodes based on search term
            nodes.forEach(node => {
                let searchText = '';
                
                if (searchType === 'label' || searchType === 'all') {
                    searchText += node.label.toLowerCase();
                }
                
                if (searchType === 'purpose' || searchType === 'all') {
                    // Extract purpose from label (between parentheses)
                    const purposeMatch = node.label.match(/\\(([^)]+)\\)/);
                    if (purposeMatch && purposeMatch[1]) {
                        searchText += purposeMatch[1].toLowerCase();
                    }
                }
                
                if (searchType === 'file' || searchType === 'all') {
                    // Extract file from label (between square brackets)
                    const fileMatch = node.label.match(/\\[([^\\]]+)\\]/);
                    if (fileMatch && fileMatch[1]) {
                        searchText += fileMatch[1].toLowerCase();
                    }
                }
                
                if (searchText.includes(searchTerm)) {
                    matches.push(node);
                }
            });

            // Display results
            if (matches.length > 0) {
                matches.forEach(node => {
                    const li = document.createElement('li');
                    li.textContent = node.label.split('\\n')[0]; // Just show the first line (function name)
                    li.style.cursor = 'pointer';
                    li.style.marginBottom = '3px';
                    li.onclick = function() {
                        // Focus on this node
                        network.focus(node.id, {
                            scale: 1.2,
                            animation: {
                                duration: 1000,
                                easingFunction: 'easeInOutQuad'
                            }
                        });
                        network.selectNodes([node.id]);
                    };
                    resultsList.appendChild(li);
                });
                searchResultsDiv.style.display = 'block';
            } else {
                const li = document.createElement('li');
                li.textContent = 'No matches found';
                resultsList.appendChild(li);
                searchResultsDiv.style.display = 'block';
            }
        }

        function resetSearch() {
            document.getElementById('node-search').value = '';
            document.getElementById('search-results').style.display = 'none';
            network.unselectAll();
        }

        // Add keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            // Ctrl+F or Cmd+F (Mac) to focus search input
            if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
                event.preventDefault(); // Prevent browser's find dialog
                document.getElementById('node-search').focus();
            }
            
            // Escape to clear search
            if (event.key === 'Escape') {
                resetSearch();
            }
        });
    </script>
    """

    modified_content = content.replace('</body>', f'{legend_html}</body>')

    with open(html_file, "w") as file:
        file.write(modified_content)

def find_asm_files(directory='.'):
    """
    Finds all .asm files in the given directory
    
    Args:
        directory (str) : Dictionary path to search

    Returns:
        list: List of .asm file paths
    """

    asm_files = []
    asm_extentions = [".asm", ".s", ".nasm", ".inc", ".mac", ".z80", ".x86", ".gas"]

    for file in os.listdir(directory):
        file_lower = file.lower()
        if any(file_lower.endswith(ext) for ext in asm_extentions):
            asm_files.append(os.path.join(directory, file))
    
    return asm_files

def create_flowchart(files=None, recursive=True, analyze_dependencies=True):
    """
    calls the functions to create the flowchart
    
    args:
        files (list) : List of file paths to parse.

    Returns:
        None
    """

    all_files = set()

    if files is None:
        files = find_asm_files()
        if not files:
            print("No assmebly files found in the current directory.")
            return
        
    #build list of files including dependencies
    all_files.update(files)

    if recursive:
        for file_path in list(all_files):
            includes = find_included_files(file_path)
            all_files.update(includes)

    #dependency analysis
    if analyze_dependencies:
        dependencies = analyze_cross_file_dependencies(all_files)
        print("File dependencies:")
        for file_name, deps in dependencies.items():
            print(f"  {file_name}:")
            if deps["provides"]:
                print(f"    Provides: {', '.join(deps['provides'])}")
            if deps["uses"]:
                print(f"    Uses: {', '.join(deps['uses'])}")
            if deps["includes"]:
                print(f"    Includes: {', '.join(deps['includes'])}")

    #create flowchart
    net = parse_assembly_code(files)
    output_file = "assembly_flowchart.html"
    net.show(output_file)

    add_fixed_legend(output_file)

    print(f"Flowchart saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if os.path.isdir(sys.argv[1]):
            create_flowchart(find_asm_files(sys.argv[1]))
        else:
            create_flowchart(sys.argv[1:])
    else:
        create_flowchart()
