# This is the executable script that will be triggered by a Windows Scheduled Task.
import time
from agents.processor_agent import ProcessorAgent
from config.settings import settings
from datetime import datetime

def run_processor_batch():
    """
    Runs a batch of idea processing.
    """
    processor_agent = ProcessorAgent()
    print(f"[{datetime.now().isoformat()}] Starting processor run...")
    run_count = settings.processing_batch_max_rerun
    delay_seconds = settings.processing_interval_minutes * 60
    while(run_count > 0):
        pending_ideas = processor_agent.scratchpad_agent.get_pending_ideas()
        
        # Also get ideas that were flagged for reprocessing
        reprocess_ideas = [idea for idea in processor_agent.scratchpad_agent.get_all_ideas() if idea['status'] == 'reprocess']
        
        ideas_to_process = (reprocess_ideas + pending_ideas)[:settings.processing_batch_size]

        if not ideas_to_process:
            print(f"[{datetime.now().isoformat()}] No new or pending ideas to process. Exiting.")
            return

        print(f"[{datetime.now().isoformat()}] Found {len(pending_ideas) + len(reprocess_ideas)} ideas in the queue. Processing a batch of {len(ideas_to_process)}.")
        
        for idea in ideas_to_process:
            print(f"[{datetime.now().isoformat()}] Processing idea: {idea['id']}")
            start_time = time.perf_counter()
            processor_agent.process_idea(idea)
            end_time = time.perf_counter()
            print(f"[{datetime.now().isoformat()}] Finished processing idea {idea['id']} in {end_time - start_time:.2f} seconds.")

        run_count = run_count - 1
        print(f"[{datetime.now().isoformat()}] Processor run finished. Rerun Count:{run_count}")
        if(run_count > 0):
            reprocess_ideas = [idea for idea in processor_agent.scratchpad_agent.get_all_ideas() if idea['status'] == 'reprocess']
            if(len(reprocess_ideas) == 0):
                break
        time.sleep(delay_seconds)


if __name__ == "__main__":
    run_processor_batch()
