# handlers/scaffolding_handler.py
import os

class ScaffoldingHandler:
    def __init__(self, dialog, scaffolding_service):
        self.dialog = dialog
        self.scaffolding = scaffolding_service

    def register(self, router):
        """Register all scaffolding intents with the router."""
        router.register(r"create (a )?project|scaffold|new project|make (a )?project", self.create_project)
        router.register(r"generate project|start project|initialize project", self.create_project)
        return self

    def create_project(self):
        """Interactive project creation using dialog manager."""
        # Step 1: Get project type
        available_types = list(self.scaffolding.available_templates.keys())
        if not available_types:
            self.dialog.speak("No project templates available.")
            return

        type_prompt = "What type of project would you like to create? Available types: " + ", ".join(available_types)
        project_type = self.dialog.listen_with_retry(type_prompt, "Please choose a project type from the list.")
        if not project_type:
            return

        # Normalize: find closest match in available_types
        matched_type = None
        for t in available_types:
            if t.lower() in project_type.lower() or project_type.lower() in t.lower():
                matched_type = t
                break
        if not matched_type:
            self.dialog.speak(f"Sorry, I don't recognise '{project_type}'. Available types: {', '.join(available_types)}")
            return
        project_type = matched_type

        # Step 2: Get project name
        project_name = self.dialog.listen_with_retry("What would you like to name your project?")
        if not project_name:
            return
        # Sanitise name: remove spaces, special chars
        project_name = "".join(c for c in project_name if c.isalnum() or c in ('-', '_')).strip()
        if not project_name:
            self.dialog.speak("Invalid project name.")
            return

        # Step 3: Ask for extra options
        self.dialog.speak("Do you want to include a database setup?")
        with_db = self.dialog.confirm("Include database?")
        self.dialog.speak("Do you want to include authentication?")
        with_auth = self.dialog.confirm("Include authentication?")

        # Build command string (as expected by service's _parse_command_options)
        command_parts = []
        if with_db:
            command_parts.append("with database")
        if with_auth:
            command_parts.append("with auth")
        command = " ".join(command_parts)

        # Step 4: Confirm and create
        confirm_msg = f"Create a {project_type} project named '{project_name}'"
        if with_db:
            confirm_msg += " with database"
        if with_auth:
            confirm_msg += " with authentication"
        confirm_msg += "?"

        if not self.dialog.confirm(confirm_msg):
            self.dialog.speak("Project creation cancelled.")
            return

        # Step 5: Call the service
        target_dir = os.path.expanduser("~/projects")  # could be configurable
        self.dialog.show_thinking()
        result = self.scaffolding.create_project(
            project_type=project_type,
            project_name=project_name,
            target_dir=target_dir,
            command=command
        )
        self.dialog.hide_thinking()

        if result.get("success"):
            self.dialog.speak(f"Project created successfully at {result['path']}")
        else:
            self.dialog.speak(f"Failed to create project: {result['message']}")