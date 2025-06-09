import logging
from e2b import Sandbox  
import os

logger = logging.getLogger(__name__)
E2B_API_KEY = os.getenv("E2B_API_KEY")

if not E2B_API_KEY:
    logger.warning("E2B_API_KEY not found. E2BExecutionService will not function.")

async def run_code_in_e2b_sandbox(code: str, language: str = "python3") -> dict:
    """
    Runs Python or Shel code in a new E2B sandbox.
    """
    if not E2B_API_KEY:
        return {"success": False, "stdout": "", "stderr": "E2B_API_KEY not configured.",
                "error_message": "E2B not configured."}

    results = {"success": False, "stdout": "", "stderr": "", "error_message": None, "artifacts": []}
    sandbox = None  

    try:
        logger.info(f"E2B: Creating sandbox for {language} execution...")
        
        template = "python3" if language.lower() == "python" else "base"
        sandbox = await Sandbox.create(template=template, api_key=E2B_API_KEY)  
        logger.info(f"E2B: Sandbox created (ID: {sandbox.id}). Timeout: {sandbox.timeout}s")

        if language.lower() == "python":
            
            filename = "script.py"
            await sandbox.filesystem.write(filename, code)
            logger.info(f"E2B: Wrote python code to {filename} in sandbox.")
            process = await sandbox.process.start(f"python {filename}")
        elif language.lower() == "shell":
            
            process = await sandbox.process.start(cmd=code)  
        else:
            results["error_message"] = f"Unsupported language: {language}"
            results["stderr"] = results["error_message"]
            return results

        logger.info(f"E2B: Process started (PID: {process.pid}). Waiting for output...")

        await process  

        results["stdout"] = process.stdout
        results["stderr"] = process.stderr

        if process.exit_code == 0:
            results["success"] = True
            logger.info(f"E2B: Process completed successfully. Exit code: {process.exit_code}")
        else:
            results["success"] = False
            results["error_message"] = f"Process exited with code {process.exit_code}"
            logger.warning(f"E2B: Process failed. Exit code: {process.exit_code}, Stderr: {process.stderr}")

    except Exception as e:
        logger.exception(f"E2B: Error during sandbox execution: {e}")
        results["error_message"] = str(e)
        results["stderr"] = str(e)
    finally:
        if sandbox:
            logger.info(f"E2B: Closing sandbox (ID: {sandbox.id})...")
            await sandbox.close()
            logger.info(f"E2B: Sandbox closed.")

    return results