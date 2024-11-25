import sys
import logging
import asyncio
from managers.agents_manager import AgentsManager
from managers.objective_manager import ObjectiveManager
from managers.aider_manager import AiderManager
from managers.agent_runner import AgentRunner
from utils.logger import Logger

def main():
    if len(sys.argv) < 2:
        print("Usage: kin <command> [options]")
        sys.exit(1)

    # Get model from command line args
    model = None  # Will be set to default in each manager if not specified
    if "--model" in sys.argv:
        try:
            model_index = sys.argv.index("--model") + 1
            model = sys.argv[model_index]
        except (ValueError, IndexError):
            print("Invalid value for --model. Using default (gpt-4o-mini)")

    command = sys.argv[1]
    
    # Route commands to appropriate managers
    if command == "generate":
        if len(sys.argv) < 3:
            print("Usage: kin generate <agents|objective|map|viz> [options]")
            sys.exit(1)

        subcommand = sys.argv[2]
        if subcommand == "map":
            manager = AiderManager()
            manager.logger.logger.setLevel(logging.DEBUG)  # Set log level to DEBUG
            manager.run_map_maintenance_for_all_folders()
            
        elif subcommand == "agents":
            manager = AgentsManager(model=model)
            # Optional mission file path
            mission_path = sys.argv[3] if len(sys.argv) > 3 else ".aider.mission.md"
            asyncio.run(manager.generate_agents(mission_path))
            
        elif subcommand == "viz":
            from managers.vision_manager import VisionManager
            manager = VisionManager()
            asyncio.run(manager.generate_visualization())
            manager = ObjectiveManager()
            
            # Parse arguments
            if len(sys.argv) < 4 or sys.argv[3] != "--agent":
                print("Usage: kin generate objective --agent <agent_name>")
                sys.exit(1)
                
            if len(sys.argv) < 5:
                print("Usage: kin generate objective --agent <agent_name>")
                sys.exit(1)
                
            agent_name = sys.argv[4]
            agent_path = f".aider.agent.{agent_name}.md"
            mission_path = ".aider.mission.md"
            
            manager.generate_objective(mission_path, agent_path)
            
            
    elif command == "run":
        if len(sys.argv) < 3:
            print("Usage: kin run <agents|aider|map> [options]")
            print("Options:")
            print("  --generate    Generate agents if missing")
            print("  --verbose     Show detailed debug information")
            print("  --mission     Specify mission file path")
            print("  --model      Specify model to use (default: gpt-4o-mini)")
            sys.exit(1)
            
        subcommand = sys.argv[2]
        if subcommand == "agents":
            # Create and initialize runner asynchronously
            async def init_and_run_agents():
                # Get model name from outer scope
                nonlocal model
                run_model = model  # Use the model from command line
                if "--model" in sys.argv:
                    try:
                        model_index = sys.argv.index("--model") + 1
                        run_model = sys.argv[model_index]
                    except (ValueError, IndexError):
                        print("Invalid value for --model. Using default (gpt-4o-mini)")

                # Use the factory method to create and initialize the runner
                runner = await AgentRunner.create(model=run_model)
                
                # Set global log level based on verbose flag
                if "--verbose" in sys.argv:
                    Logger.set_global_level(logging.DEBUG)
                else:
                    Logger.set_global_level(logging.SUCCESS)
                    
                # Get mission file path
                mission_path = ".aider.mission.md"  # default
                if "--mission" in sys.argv:
                    try:
                        mission_index = sys.argv.index("--mission") + 1
                        if mission_index < len(sys.argv):
                            mission_path = sys.argv[mission_index]
                    except (ValueError, IndexError):
                        print("Missing value for --mission flag")
                        sys.exit(1)
                    
                # Get agent count
                agent_count = 5  # Default value
                if "--count" in sys.argv:
                    try:
                        count_index = sys.argv.index("--count") + 1
                        agent_count = int(sys.argv[count_index])
                    except (ValueError, IndexError):
                        print("Invalid value for --count. Using default (5)")

                # Get model name
                model = None  # Will use default from command line
                if "--model" in sys.argv:
                    try:
                        model_index = sys.argv.index("--model") + 1
                        model = sys.argv[model_index]
                    except (ValueError, IndexError):
                        print("Invalid value for --model. Using default model")
                
                # Check for --generate flag    
                should_generate = "--generate" in sys.argv
                
                # Display startup message
                runner.logger.success("🌟 Starting KinOS...")

                # Run with the initialized runner
                await runner.run(
                    mission_path, 
                    generate_agents=should_generate,
                    agent_count=agent_count,
                    model=model
                )

            # Run the async initialization and execution
            asyncio.run(init_and_run_agents())
            
        elif subcommand == "aider":
            manager = AiderManager()
            
            # Parse arguments
            if len(sys.argv) < 4 or sys.argv[3] != "--agent":
                print("Usage: kin run aider --agent <agent_name>")
                sys.exit(1)
                
            if len(sys.argv) < 5:
                print("Usage: kin run aider --agent <agent_name>")
                sys.exit(1)
                
            agent_name = sys.argv[4]
            
            # Use default paths based on agent name
            agent_path = f".aider.agent.{agent_name}.md"
            objective_path = f".aider.objective.{agent_name}.md"  # Default objective path
            map_path = f".aider.map.{agent_name}.md"  # Default map path
            
            manager.run_aider(
                objective_filepath=objective_path,
                agent_filepath=agent_path
            )
            
    elif command == "interactive":
        from managers.interactive_manager import InteractiveManager
        manager = InteractiveManager(model=model)
        asyncio.run(manager.start_session())
            
    elif command == "redundancy":
        if len(sys.argv) < 3:
            print("Usage: kin redundancy <analyze|add|report|delete|reset> [options]")
            print("\nCommands:")
            print("  analyze    Analyze files for redundancy")
            print("  add       Add files to redundancy database")
            print("  report    Generate redundancy report")
            print("  reset     Clear all data from redundancy database")
            print("\nOptions:")
            print("  --file    Specify single file")
            print("  --threshold  Set similarity threshold (0.0-1.0)")
            print("  --output  Specify output file for report")
            sys.exit(1)

        from managers.redundancy_manager import RedundancyManager
        manager = RedundancyManager(model=model)
        
        subcommand = sys.argv[2]
        
        if subcommand == "analyze":
            # Parse options
            file_path = None
            threshold = 0.85
            
            if "--file" in sys.argv:
                try:
                    file_index = sys.argv.index("--file") + 1
                    file_path = sys.argv[file_index]
                except IndexError:
                    print("Missing value for --file")
                    sys.exit(1)
                    
            if "--threshold" in sys.argv:
                try:
                    threshold_index = sys.argv.index("--threshold") + 1
                    threshold = float(sys.argv[threshold_index])
                except (IndexError, ValueError):
                    print("Invalid value for --threshold")
                    sys.exit(1)
            
            # Set log level to INFO to see more details
            manager.logger.logger.setLevel(logging.INFO)
            
            # Perform analysis
            if file_path:
                manager.logger.info(f"🔍 Analyzing single file: {file_path}")
                results = manager.analyze_file(file_path, threshold)
                manager.logger.info(f"✨ Analysis complete for {file_path}")
            else:
                manager.logger.info("🔍 Starting full project analysis...")
                results = manager.analyze_all_files(threshold)
                manager.logger.info(f"✨ Project analysis complete")
                
            # Generate and save report
            manager.logger.info("📝 Generating redundancy report...")
            report = manager.generate_redundancy_report(results)
            output_file = "redundancy_report.md"
            
            if "--output" in sys.argv:
                try:
                    output_index = sys.argv.index("--output") + 1
                    output_file = sys.argv[output_index]
                except IndexError:
                    print("Missing value for --output")
                    sys.exit(1)
                    
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
                
            # Show summary
            stats = results.get('statistics', {})
            manager.logger.success(
                f"\n📊 Analysis Summary:\n"
                f"   - Files analyzed: {stats.get('files_analyzed', 0)}\n"
                f"   - Total paragraphs: {stats.get('total_paragraphs', 0)}\n"
                f"   - Redundant paragraphs: {stats.get('redundant_paragraphs', 0)}\n"
                f"   - Redundancy clusters: {stats.get('cluster_count', 0)}"
            )
            manager.logger.success(f"\n📄 Report saved to: {output_file}")
            
        elif subcommand == "add":
            # Parse file option
            file_path = None
            if "--file" in sys.argv:
                try:
                    file_index = sys.argv.index("--file") + 1
                    file_path = sys.argv[file_index]
                except IndexError:
                    print("Missing value for --file")
                    sys.exit(1)
            
            # Set log level to INFO to see more details
            manager.logger.logger.setLevel(logging.INFO)
            
            # Add content
            if file_path:
                manager.add_file(file_path)
            else:
                stats = manager.add_all_files()
                manager.logger.success(
                    f"✨ Added {stats['total_paragraphs']} paragraphs from {stats['total_files']} files"
                )
                if stats['errors']:
                    manager.logger.warning("\n⚠️ Errors encountered:")
                    for error in stats['errors']:
                        manager.logger.warning(f"   - {error['file']}: {error['error']}")
                
        elif subcommand == "report":
            # Generate report from existing database
            results = manager.analyze_all_files()
            report = manager.generate_redundancy_report(results)
            
            output_file = "redundancy_report.md"
            if "--output" in sys.argv:
                try:
                    output_index = sys.argv.index("--output") + 1
                    output_file = sys.argv[output_index]
                except IndexError:
                    print("Missing value for --output")
                    sys.exit(1)
                    
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
                
            print(f"Report generated and saved to {output_file}")
            
        elif subcommand == "delete":
                # Parse options
                auto_mode = "--auto" in sys.argv
                dry_run = "--dry-run" in sys.argv
                interactive = "--interactive" in sys.argv
                threshold = 0.95  # Default threshold for auto mode
                    
                if "--threshold" in sys.argv:
                    try:
                        threshold_index = sys.argv.index("--threshold") + 1
                        threshold = float(sys.argv[threshold_index])
                    except (IndexError, ValueError):
                        print("Invalid value for --threshold")
                        sys.exit(1)
                    
                # Set strategy for which version to keep
                keep_strategy = "longest"  # Default strategy
                if "--keep-first" in sys.argv:
                    keep_strategy = "first"
                        
                # Set verbose logging if requested
                if "--verbose" in sys.argv:
                    manager.logger.logger.setLevel(logging.DEBUG)
                    print("🔍 Verbose logging enabled")
                        
                # Perform deletion
                if not any([auto_mode, interactive]):
                    print("Please specify either --auto or --interactive mode")
                    print("\nOptions:")
                    print("  --auto         Automatically delete duplicates")
                    print("  --interactive  Review and select which duplicates to delete")
                    print("  --threshold    Set similarity threshold (default: 0.95)")
                    print("  --keep-longest Keep longest version (default)")
                    print("  --keep-first   Keep first occurrence")
                    print("  --dry-run      Show what would be deleted without making changes")
                    print("  --verbose      Show detailed debug information")
                    sys.exit(1)
                    
                results = manager.delete_duplicates(
                    auto_mode=auto_mode,
                    interactive=interactive,
                    threshold=threshold,
                    keep_strategy=keep_strategy,
                    dry_run=dry_run
                )
                
                # Show results
                if dry_run:
                    print("\nDry run - no changes made")
                print(f"\nResults:")
                print(f"- Files modified: {results['files_modified']}")
                print(f"- Duplicates removed: {results['duplicates_removed']}")
                if results['errors']:
                    print("\nErrors encountered:")
                    for error in results['errors']:
                        print(f"- {error}")

        elif subcommand == "reset":
            # Reset the redundancy database
            manager = RedundancyManager(model=model)
            manager._reset_collection()
            print("✨ Redundancy database has been reset")
        else:
            print(f"Unknown redundancy command: {subcommand}")
            sys.exit(1)
            
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
