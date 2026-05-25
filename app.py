import json
import tempfile
from pathlib import Path

import gradio as gr

from core import (
    count_file,
    count_files_batch,
    SUPPORTED_EXTENSIONS,
)


# =============================================================================
# HELPERS
# =============================================================================

SUPPORTED_LABEL = ", ".join(sorted(SUPPORTED_EXTENSIONS))


def format_number(n: int) -> str:
    return f"{n:,}"


def single_result_to_markdown(result):
    return f"""
# File Analysis

| Metric | Value |
|---|---|
| Filename | `{result.filename}` |
| Status | `{result.status}` |
| File Type | `{result.file_type}` |
| Pages | `{format_number(result.pages)}` |
| Extractable Pages | `{format_number(result.extractable_pages)}` |
| Skipped Pages | `{format_number(result.skipped_pages)}` |
| Characters | `{format_number(result.char_count)}` |
| Words | `{format_number(result.word_count)}` |
| GPT Tokens | `{format_number(result.gpt_tokens)}` |
| Processing Time | `{result.elapsed_sec:.2f}s` |

"""

def batch_result_to_markdown(batch):
    return f"""
# Batch Analysis

| Metric | Value |
|---|---|
| Files Processed | `{format_number(batch.file_count)}` |
| Errors | `{format_number(batch.error_count)}` |
| Total Pages | `{format_number(batch.total_pages)}` |
| Total Extractable Pages | `{format_number(batch.total_extractable_pages)}` |
| Total Skipped Pages | `{format_number(batch.total_skipped_pages)}` |
| Total Characters | `{format_number(batch.total_chars)}` |
| Total Words | `{format_number(batch.total_words)}` |
| Total GPT Tokens | `{format_number(batch.total_tokens)}` |
| Total Processing Time | `{batch.elapsed_sec:.2f}s` |

"""

def result_to_json(result):
    return {
        "filename": result.filename,
        "status": result.status,
        "file_type": result.file_type,
        "pages": result.pages,
        "extractable_pages": result.extractable_pages,
        "skipped_pages": result.skipped_pages,
        "char_count": result.char_count,
        "word_count": result.word_count,
        "gpt_tokens": result.gpt_tokens,
        "elapsed_sec": result.elapsed_sec,
        "error_msg": result.error_msg,
    }


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def analyze_files(files):

    if not files:
        return (
            "# No files uploaded",
            None,
        )

    paths = [f.name for f in files]

    # Single file mode
    if len(paths) == 1:

        result = count_file(paths[0])

        md = single_result_to_markdown(result)

        json_output = json.dumps(
            result_to_json(result),
            indent=2,
        )

        return md, json_output

    # Batch mode
    batch = count_files_batch(paths)

    md = batch_result_to_markdown(batch)

    detailed = []

    for file_result in batch.files:
        detailed.append(result_to_json(file_result))

    json_output = json.dumps(
        {
            "summary": {
                "file_count": batch.file_count,
                "error_count": batch.error_count,
                "total_pages": batch.total_pages,
                "total_extractable_pages": batch.total_extractable_pages,
                "total_skipped_pages": batch.total_skipped_pages,
                "total_chars": batch.total_chars,
                "total_words": batch.total_words,
                "total_tokens": batch.total_tokens,
                "elapsed_sec": batch.elapsed_sec,
            },
            "files": detailed,
        },
        indent=2,
    )

    return md, json_output


# =============================================================================
# UI
# =============================================================================

with gr.Blocks(
    title="Production Token Counter",
    theme=gr.themes.Soft(),
) as demo:

    gr.Markdown(
        """
# Production-Grade Token Counter

Analyze:
- PDF
- TXT
- MD
- DOCX
- PPTX

Features:
- Real GPT token counting using `tiktoken`
- Streaming architecture
- Scanned PDF detection
- Large file support
- Batch processing
"""
    )

    with gr.Row():

        file_input = gr.File(
            label=f"Upload Files ({SUPPORTED_LABEL})",
            file_count="multiple",
            type="filepath",
        )

    analyze_btn = gr.Button(
        "Analyze Tokens",
        variant="primary",
    )

    with gr.Row():

        markdown_output = gr.Markdown()

    with gr.Row():

        json_output = gr.Code(
            label="JSON Output",
            language="json",
        )

    analyze_btn.click(
        fn=analyze_files,
        inputs=[file_input],
        outputs=[
            markdown_output,
            json_output,
        ],
    )

    gr.Markdown(
        """
### Notes

- Uses real GPT tokenizer (`cl100k_base`)
- Scanned/image-only PDFs are skipped
- Optimized for very large documents
- Batch processing supported
"""
    )


# =============================================================================
# ENTRYPOINT
# =============================================================================

if __name__ == "__main__":
    demo.launch()