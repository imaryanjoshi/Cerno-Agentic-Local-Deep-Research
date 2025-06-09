import re
from pathlib import Path
import argparse

LOG_FILE_PATH = Path(__file__).resolve().parent / "agno_metrics.log"  

PRICE_PER_INPUT_TOKEN = 0.15 / 1_000_000
PRICE_PER_OUTPUT_TOKEN = 0.60 / 1_000_000

METRICS_BLOCK_REGEX = re.compile(
    r"DEBUG \*{80}  METRICS  \*{80}\n"  
    r".*?\* Tokens:\s*input=(\d+),\s*output=(\d+)"  
    
    , re.DOTALL  
)

def calculate_cost_from_log(log_file_path: Path) -> tuple[int, int, float]:
    """
    Parses the log file, extracts token counts from METRICS blocks,
    and calculates the total cost.

    Returns:
        A tuple: (total_input_tokens, total_output_tokens, total_cost)
    """
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0

    if not log_file_path.exists():
        print(f"Error: Log file not found at {log_file_path}")
        return 0, 0, 0.0

    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_content = f.read()
    except Exception as e:
        print(f"Error reading log file {log_file_path}: {e}")
        return 0, 0, 0.0

    matches = METRICS_BLOCK_REGEX.finditer(log_content)

    call_count = 0
    for match in matches:
        call_count += 1
        try:
            input_tokens = int(match.group(1))
            output_tokens = int(match.group(2))

            total_input_tokens += input_tokens
            total_output_tokens += output_tokens

            call_cost = (input_tokens * PRICE_PER_INPUT_TOKEN) + \
                        (output_tokens * PRICE_PER_OUTPUT_TOKEN)
            total_cost += call_cost

            print(
                f"  LLM Call {call_count}: Input Tokens: {input_tokens}, Output Tokens: {output_tokens}, Cost: ${call_cost:.6f}")

        except ValueError:
            print(f"Warning: Could not parse tokens in match: {match.groups()}")
        except Exception as e:
            print(f"Warning: Error processing match: {e}")

    if call_count == 0:
        print("No METRICS blocks found in the log file. Ensure 'agno' logger is set to DEBUG.")

    return total_input_tokens, total_output_tokens, total_cost

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate LLM run cost from agno_metrics.log.")
    parser.add_argument(
        "--log_file",
        type=Path,
        default=LOG_FILE_PATH,
        help=f"Path to the agno_metrics.log file (default: {LOG_FILE_PATH})"
    )
    args = parser.parse_args()

    print(f"Calculating cost from log file: {args.log_file}\n")

    total_input, total_output, final_cost = calculate_cost_from_log(args.log_file)

    print("\n--- Total Calculation ---")
    print(f"Total Input Tokens:  {total_input}")
    print(f"Total Output Tokens: {total_output}")
    print(f"Estimated Total Cost: ${final_cost:.6f}")