
### Courtesy of o1-preview (ChatGPT and Gemini failed on this)
### See pyparser-examples.txt for complex examples

import codeop

def parse_code(x):
    x = x.lstrip('\n')
    lines = x.split('\n')
    blocks = []
    buffer = ''
    compiler = codeop.CommandCompiler()
    for i, line in enumerate(lines):
        if buffer == '':
            buffer = line
        else:
            buffer += '\n' + line
        try:
            code_compiled = compiler(buffer)
            if code_compiled:
                # Compilation succeeded, buffer is a complete code block.
                blocks.append(buffer)
                buffer = ''
        except (SyntaxError, ValueError):
            # Not complete yet, continue to read more lines.
            continue
    # If buffer is not empty, append it as a block.
    if buffer.strip():
        blocks.append(buffer)

    filtered_blocks = [block for block in blocks if block]   # remove ''
    return filtered_blocks

