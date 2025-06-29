"""
Quick Demo: Zen-MCP Automated Code Management

This script demonstrates the automation system in action.
"""

import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)
import sys
from pathlib import Path

# Add automation directory to path
sys.path.insert(0, str(Path(__file__).parent))

from automation.zen_code_automation import ZenCodeAutomation


async def demo():
    """Run a quick demonstration of the automation system"""
    logger.info("🎯 Zen-MCP Automated Code Management Demo")
    logger.info("=" * 50)
    
    # Initialize automation
    automation = ZenCodeAutomation()
    
    # Check zen-mcp-server status
    logger.info("\n1️⃣ Checking zen-mcp-server status...")
    session = await automation._get_session()
    try:
        async with session.get(f"{automation.zen_url}/version") as response:
            if response.status == 200:
                logger.info("✅ zen-mcp-server is running!")
            else:
                logger.info("❌ zen-mcp-server is not responding")
                return
    except Exception as e:
        logger.info(f"❌ Cannot connect to zen-mcp-server: {e}")
        logger.info("\nPlease ensure zen-mcp-server is running:")
        logger.info("  cd zen-mcp-server")
        logger.info("  .zen_venv\\Scripts\\python.exe server.py")
        return
    
    # Create a sample file for analysis
    logger.info("\n2️⃣ Creating sample code for analysis...")
    sample_file = Path("temp/sample_code.py")
    sample_file.parent.mkdir(exist_ok=True)
    
    sample_code = '''
# Sample code with various issues for demonstration

def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price'] * item['quantity']
    return total

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, input_data):
        # TODO: Add error handling
        result = []
        for d in input_data:
            if d > 0:
                result.append(d * 2)
        return result
    
    def save_to_file(self, filename):
        f = open(filename, 'w')
        f.write(str(self.data))
        f.close()

# Security issue: using eval
def execute_command(cmd):
    return eval(cmd)

# Performance issue: inefficient string concatenation
def build_report(data):
    report = ""
    for item in data:
        report = report + str(item) + "\\n"
    return report
'''
    
    with open(sample_file, 'w') as f:
        f.write(sample_code)
    
    logger.info(f"✅ Created sample file: {sample_file}")
    
    # Analyze the file
    logger.info("\n3️⃣ Analyzing code for improvements...")
    tasks = await automation._analyze_file(sample_file)
    
    logger.info(f"\n📊 Analysis Results:")
    logger.info(f"Found {len(tasks)} improvement opportunities:\n")
    
    for i, task in enumerate(tasks[:5], 1):  # Show first 5 tasks
        logger.info(f"{i}. [{task.priority.name}] {task.type}")
        logger.info(f"   📝 {task.description}")
        logger.info()
    
    # Execute one improvement
    if tasks:
        logger.info("\n4️⃣ Applying an improvement...")
        high_priority_task = next((t for t in tasks if t.priority.value <= 2), tasks[0])
        
        logger.info(f"Executing: {high_priority_task.description}")
        success = await automation.execute_task(high_priority_task)
        
        if success:
            logger.info("✅ Improvement applied successfully!")
            logger.info(f"   Check the backup in: backups/")
            logger.info(f"   Modified file: {high_priority_task.file_path}")
        else:
            logger.info("❌ Failed to apply improvement")
    
    # Generate report
    logger.info("\n5️⃣ Generating improvement report...")
    await automation.generate_improvement_report()
    logger.info(f"✅ Report saved to: reports/")
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ Demo Complete!")
    logger.info("\nThe automation system can:")
    logger.info("  • Continuously scan your codebase")
    logger.info("  • Identify security vulnerabilities")
    logger.info("  • Optimize performance")
    logger.info("  • Improve code quality")
    logger.info("  • Generate documentation")
    logger.info("  • Track ML model performance")
    logger.info("\nTo run continuously, use: start_automation.bat")
    logger.info("To monitor progress, use: start_dashboard.bat")
    
    await automation.close()


if __name__ == "__main__":
    asyncio.run(demo())