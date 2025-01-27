from icecream import ic
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
import asyncio

console = Console()

async def main():
    with Live(console=console, refresh_per_second=4) as live:
        # Test icecream
        ic("Testing icecream output")
        await asyncio.sleep(1)
        
        # Test rich live display
        live.update(Panel("Testing Rich live display"))
        await asyncio.sleep(1)
        
        print("Environment test complete")

if __name__ == "__main__":
    asyncio.run(main())
