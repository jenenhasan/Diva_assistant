import json
import os
import subprocess
import re
from json.decoder import JSONDecodeError
#add feature for creating a uml digrams from the project code or idea 
class ScaffoldingManager:
    """Handles project scaffolding and template management"""
    
    DEPENDENCY_MAP = {
        "flask-project": {
            "manager": "pip",
            "packages": ["flask", "python-dotenv"]
        },
        "django-project": {
            "manager": "pip", 
            "packages": ["django"]
        },
        "fastapi-project": {
            "manager": "pip",
            "packages": ["fastapi", "uvicorn"]
        }
    }

    



    def __init__(self):
        #self.template_path = template_path
        self.current_project = None
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(current_dir, 'templates.json')
        
        self.available_templates = self._load_templates()
        if not os.path.exists(self.json_path):
            print(f"Error: The templates.json file was not found at {self.json_path}")
            self.available_templates = {}

#####################parse commands ################################################################



        
       

    def _parse_command_options(self, command):
        """Extract options from voice command string"""
        command = command.lower()
        return {
            "database": "with database" in command,
            "auth": "with auth" in command,
            "exclude_folders": self._get_excluded_folders(command)
        }
    def parse_schaf_command(self, text: str) -> dict:
        text = text.lower().strip()
        params = {
        'type': None,
        'name': None,
        'options': {
            'database': False,
            'auth': False,
            'exclude_folders': []
        }
        }
        for template , config in self.available_templates.items():
            search_terms = [template] + config.get('aliases', [])
            if any(term in text for term in search_terms):
                params['type'] = template
                break
        name_match = re.search(r'(?:named|called|name is|is called)\s+(.+?)(?:\s+with|\s+exclude|$)',text)
        if name_match:
            params['name'] = name_match.group(1).strip()

        params['options']['database'] = bool(re.search(r'\b(?:with\s+)?database\b', text))
        params['options']['auth'] = bool(re.search(r'\b(?:with\s+)?auth(?:entication)?\b', text))

        exclude_match = re.search(r'exclude\s+(.+)', text)
        if exclude_match:
            params['options']['exclude_folders'] = [
                f.strip() 
                for f in re.split(r'[,\s]+', exclude_match.group(1)) 
                if f.strip()
                ]
            
        return params


    

 
    
    
    
###########################################################################################

    def _load_templates(self):
        """Load project templates from JSON file"""
        try:
            with open(self.json_path, "r") as f:
                templates = json.load(f)
                for name in templates:
                    templates[name].setdefault("aliases", [])
                return templates
        except (FileNotFoundError, JSONDecodeError) as e:
            print(f"Error loading templates: {str(e)}")
            return {}
        
    def _get_excluded_folders(self, command):
        """Parse excluded folders from command"""
        if "exclude" not in command:
            return []
        return [f.strip() for f in command.split("exclude")[1].split(",")]

    def _generate_requirements(self, project_type, project_path):
        """Generate requirements.txt file for the project"""
        if project_type not in self.DEPENDENCY_MAP:
            return False
            
        with open(os.path.join(project_path, "requirements.txt"), "w") as f:
            packages = self.DEPENDENCY_MAP[project_type]["packages"]
            f.write("\n".join(packages))
        return True

    def _create_readme(self, project_type, project_path):
        """Generate basic README file"""
        content = f"""# {project_type.replace('-', ' ').title()} Project\n\n"""
        content += "## Setup Instructions\n"
        content += "```bash\npython -m venv venv\nsource venv/bin/activate\npip install -r requirements.txt\n```"
        
        with open(os.path.join(project_path, "README.md"), "w") as f:
            f.write(content)

    def _install_packages(self, project_type, project_path):
        """Install project dependencies using subprocess"""
        if project_type not in self.DEPENDENCY_MAP:
            return False

        try:
            subprocess.run(
                [
                    self.DEPENDENCY_MAP[project_type]["manager"],
                    "install",
                    *self.DEPENDENCY_MAP[project_type]["packages"]
                ],
                check=True,
                cwd=project_path
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Package installation failed: {str(e)}")
            return False

    def create_project(self, project_type, project_name, target_dir, command=""):
        """Main method to create a new project"""
        
        if project_type not in self.available_templates:
            return {'success' : False , 'message' : f"Invalid template. Available: {', '.join(self.available_templates.keys())}"}
        

        project_path = os.path.join(target_dir, project_name)
        if os.path.exists(project_path):
            return {'success' : False  , 'message' : f"Project '{project_name}' already exists!"}
        
        os.makedirs(project_path, exist_ok=True)
        options = self._parse_command_options(command)
        template = self.available_templates[project_type]

        # Create directory structure
        for folder in template.get('folders', []):
            if folder not in options['exclude_folders']:
                os.makedirs(os.path.join(project_path, folder), exist_ok=True)

        # Create base files
        for file_path in template.get('files', []):
            full_path = os.path.join(project_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            open(full_path, 'a').close()

        # Add optional components
        if options["database"]:
            db_path = os.path.join(project_path, "config", "database.py")
            with open(db_path, "w") as f:
                f.write("# Database configuration\n")

        if options["auth"]:
            auth_path = os.path.join(project_path, "app", "auth.py")
            with open(auth_path, "w") as f:
                f.write("# Authentication module\n")

        # Generate supporting files
        self._generate_requirements(project_type, project_path)
        self._create_readme(project_type, project_path)
        
        # Install dependencies
        success = self._install_packages(project_type, project_path)
        self.current_project = project_path if success else None
        
        return {'success': True, 'message': f"Project created at {project_path}", 'path': project_path}

# Example usage:
if __name__ == "__main__":
    scaffolder = ScaffoldingManager()
    
    # Create a Flask project
    result = scaffolder.create_project(
        project_type="fastapi-project",
        project_name="senior_project",
        target_dir=os.path.expanduser("~/projects"),
        command="with database and auth, exclude templates"
    )
    
    print(result)