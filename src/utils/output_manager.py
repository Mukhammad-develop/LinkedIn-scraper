"""
Step 4: Multiple Output Formats Manager
Support for JSON, CSV, Excel, XML, and custom templates
"""

import json
import csv
import xml.etree.ElementTree as ET
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import pandas as pd
from jinja2 import Template, Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class OutputFormat:
    """Supported output formats"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "xlsx"
    XML = "xml"
    HTML = "html"
    YAML = "yaml"
    TEMPLATE = "template"


class OutputManager:
    """Comprehensive output manager for multiple formats"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize output manager
        
        Args:
            template_dir: Directory containing custom templates
        """
        self.template_dir = template_dir or "templates"
        self.jinja_env = None
        
        # Set up Jinja2 environment if template directory exists
        if os.path.exists(self.template_dir):
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=True
            )
    
    def save_data(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                  output_path: str, format_type: str = None, **kwargs) -> bool:
        """
        Save data in specified format
        
        Args:
            data: Data to save (single profile or list of profiles)
            output_path: Output file path
            format_type: Output format (auto-detected from extension if None)
            **kwargs: Additional format-specific options
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Auto-detect format from file extension
            if format_type is None:
                format_type = self._detect_format(output_path)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Convert single profile to list for consistent processing
            if isinstance(data, dict):
                data_list = [data]
            else:
                data_list = data
            
            # Save based on format
            if format_type == OutputFormat.JSON:
                return self._save_json(data, output_path, **kwargs)
            elif format_type == OutputFormat.CSV:
                return self._save_csv(data_list, output_path, **kwargs)
            elif format_type == OutputFormat.EXCEL:
                return self._save_excel(data_list, output_path, **kwargs)
            elif format_type == OutputFormat.XML:
                return self._save_xml(data_list, output_path, **kwargs)
            elif format_type == OutputFormat.HTML:
                return self._save_html(data_list, output_path, **kwargs)
            elif format_type == OutputFormat.YAML:
                return self._save_yaml(data, output_path, **kwargs)
            elif format_type == OutputFormat.TEMPLATE:
                return self._save_template(data_list, output_path, **kwargs)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            logger.error(f"Failed to save data in {format_type} format: {e}")
            return False
    
    def _detect_format(self, output_path: str) -> str:
        """Detect format from file extension"""
        extension = Path(output_path).suffix.lower()
        
        format_map = {
            '.json': OutputFormat.JSON,
            '.csv': OutputFormat.CSV,
            '.xlsx': OutputFormat.EXCEL,
            '.xls': OutputFormat.EXCEL,
            '.xml': OutputFormat.XML,
            '.html': OutputFormat.HTML,
            '.htm': OutputFormat.HTML,
            '.yaml': OutputFormat.YAML,
            '.yml': OutputFormat.YAML,
        }
        
        return format_map.get(extension, OutputFormat.JSON)
    
    def _save_json(self, data: Any, output_path: str, **kwargs) -> bool:
        """Save data as JSON"""
        try:
            indent = kwargs.get('indent', 2)
            ensure_ascii = kwargs.get('ensure_ascii', False)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)
            
            logger.info(f"Successfully saved JSON to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            return False
    
    def _save_csv(self, data_list: List[Dict[str, Any]], output_path: str, **kwargs) -> bool:
        """Save data as CSV"""
        try:
            if not data_list:
                logger.warning("No data to save to CSV")
                return False
            
            # Flatten nested data for CSV
            flattened_data = [self._flatten_dict(profile) for profile in data_list]
            
            # Get all possible fieldnames
            fieldnames = set()
            for profile in flattened_data:
                fieldnames.update(profile.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            # Custom field order if specified
            field_order = kwargs.get('field_order', [])
            if field_order:
                ordered_fields = [f for f in field_order if f in fieldnames]
                remaining_fields = [f for f in fieldnames if f not in field_order]
                fieldnames = ordered_fields + sorted(remaining_fields)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if kwargs.get('include_header', True):
                    writer.writeheader()
                
                for profile in flattened_data:
                    # Fill missing fields with empty strings
                    row = {field: profile.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            logger.info(f"Successfully saved CSV to {output_path} with {len(data_list)} profiles")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
            return False
    
    def _save_excel(self, data_list: List[Dict[str, Any]], output_path: str, **kwargs) -> bool:
        """Save data as Excel file"""
        try:
            if not data_list:
                logger.warning("No data to save to Excel")
                return False
            
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                
                # Main profile data sheet
                flattened_data = [self._flatten_dict(profile) for profile in data_list]
                df_main = pd.DataFrame(flattened_data)
                df_main.to_excel(writer, sheet_name='Profiles', index=False)
                
                # Separate sheets for list data if requested
                if kwargs.get('separate_sheets', True) and len(data_list) == 1:
                    profile = data_list[0]
                    
                    # Experience sheet
                    if 'experience' in profile and isinstance(profile['experience'], list):
                        exp_data = []
                        for i, exp in enumerate(profile['experience']):
                            if isinstance(exp, dict):
                                exp_data.append(exp)
                            else:
                                exp_data.append({'index': i, 'description': str(exp)})
                        
                        if exp_data:
                            df_exp = pd.DataFrame(exp_data)
                            df_exp.to_excel(writer, sheet_name='Experience', index=False)
                    
                    # Education sheet
                    if 'education' in profile and isinstance(profile['education'], list):
                        edu_data = []
                        for i, edu in enumerate(profile['education']):
                            if isinstance(edu, dict):
                                edu_data.append(edu)
                            else:
                                edu_data.append({'index': i, 'description': str(edu)})
                        
                        if edu_data:
                            df_edu = pd.DataFrame(edu_data)
                            df_edu.to_excel(writer, sheet_name='Education', index=False)
                    
                    # Skills sheet
                    if 'skills' in profile and isinstance(profile['skills'], list):
                        skills_data = [{'skill': skill} for skill in profile['skills']]
                        if skills_data:
                            df_skills = pd.DataFrame(skills_data)
                            df_skills.to_excel(writer, sheet_name='Skills', index=False)
                
                # Quality report sheet if available
                if len(data_list) == 1 and 'quality_report' in data_list[0]:
                    quality_data = data_list[0]['quality_report']
                    df_quality = pd.DataFrame([quality_data])
                    df_quality.to_excel(writer, sheet_name='Quality_Report', index=False)
            
            logger.info(f"Successfully saved Excel to {output_path} with {len(data_list)} profiles")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save Excel: {e}")
            return False
    
    def _save_xml(self, data_list: List[Dict[str, Any]], output_path: str, **kwargs) -> bool:
        """Save data as XML"""
        try:
            root = ET.Element("linkedin_profiles")
            root.set("count", str(len(data_list)))
            root.set("generated_at", datetime.now().isoformat())
            
            for i, profile in enumerate(data_list):
                profile_elem = ET.SubElement(root, "profile")
                profile_elem.set("index", str(i))
                
                self._dict_to_xml(profile, profile_elem)
            
            # Create XML tree and write to file
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)  # Pretty print
            
            with open(output_path, 'wb') as f:
                tree.write(f, encoding='utf-8', xml_declaration=True)
            
            logger.info(f"Successfully saved XML to {output_path} with {len(data_list)} profiles")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save XML: {e}")
            return False
    
    def _save_html(self, data_list: List[Dict[str, Any]], output_path: str, **kwargs) -> bool:
        """Save data as HTML"""
        try:
            template_name = kwargs.get('template', 'default_profile.html')
            
            # Use custom template if available
            if self.jinja_env:
                try:
                    template = self.jinja_env.get_template(template_name)
                    html_content = template.render(profiles=data_list, **kwargs)
                except Exception as e:
                    logger.warning(f"Failed to use custom template {template_name}: {e}")
                    html_content = self._generate_default_html(data_list, **kwargs)
            else:
                html_content = self._generate_default_html(data_list, **kwargs)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Successfully saved HTML to {output_path} with {len(data_list)} profiles")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save HTML: {e}")
            return False
    
    def _save_yaml(self, data: Any, output_path: str, **kwargs) -> bool:
        """Save data as YAML"""
        try:
            import yaml
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"Successfully saved YAML to {output_path}")
            return True
            
        except ImportError:
            logger.error("PyYAML not installed. Install with: pip install pyyaml")
            return False
        except Exception as e:
            logger.error(f"Failed to save YAML: {e}")
            return False
    
    def _save_template(self, data_list: List[Dict[str, Any]], output_path: str, **kwargs) -> bool:
        """Save data using custom template"""
        try:
            template_name = kwargs.get('template_name')
            if not template_name:
                raise ValueError("template_name is required for template format")
            
            if not self.jinja_env:
                raise ValueError("Template directory not found or not set")
            
            template = self.jinja_env.get_template(template_name)
            content = template.render(profiles=data_list, **kwargs)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully saved template output to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            return False
    
    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV output"""
        items = []
        
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep=sep).items())
            elif isinstance(value, list):
                # Convert list to string or create separate columns
                if all(isinstance(item, str) for item in value):
                    items.append((new_key, '; '.join(value)))
                else:
                    # For complex list items, convert to JSON string
                    items.append((new_key, json.dumps(value, default=str)))
            else:
                items.append((new_key, str(value) if value is not None else ''))
        
        return dict(items)
    
    def _dict_to_xml(self, data: Dict[str, Any], parent_elem: ET.Element):
        """Convert dictionary to XML elements"""
        for key, value in data.items():
            # Clean key for XML element name
            clean_key = self._clean_xml_key(key)
            
            if isinstance(value, dict):
                child_elem = ET.SubElement(parent_elem, clean_key)
                self._dict_to_xml(value, child_elem)
            elif isinstance(value, list):
                list_elem = ET.SubElement(parent_elem, clean_key)
                list_elem.set("type", "list")
                list_elem.set("count", str(len(value)))
                
                for i, item in enumerate(value):
                    item_elem = ET.SubElement(list_elem, "item")
                    item_elem.set("index", str(i))
                    
                    if isinstance(item, dict):
                        self._dict_to_xml(item, item_elem)
                    else:
                        item_elem.text = str(item) if item is not None else ""
            else:
                elem = ET.SubElement(parent_elem, clean_key)
                elem.text = str(value) if value is not None else ""
    
    def _clean_xml_key(self, key: str) -> str:
        """Clean key for XML element name"""
        # Replace invalid characters with underscores
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', str(key))
        
        # Ensure it starts with a letter or underscore
        if cleaned and not cleaned[0].isalpha() and cleaned[0] != '_':
            cleaned = f"item_{cleaned}"
        
        return cleaned or "unknown"
    
    def _generate_default_html(self, data_list: List[Dict[str, Any]], **kwargs) -> str:
        """Generate default HTML template"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LinkedIn Profile Data</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .profile { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .profile h2 { color: #0066cc; margin-top: 0; }
        .profile h3 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 5px; }
        .profile p { margin: 10px 0; }
        .profile .url { color: #666; font-style: italic; }
        .profile .quality { background: #f0f8ff; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .profile ul { list-style-type: none; padding: 0; }
        .profile li { background: #f9f9f9; margin: 5px 0; padding: 8px; border-radius: 4px; }
        .header { text-align: center; margin-bottom: 30px; }
        .stats { background: #e8f4fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>LinkedIn Profile Data Export</h1>
        <p>Generated on {{ generated_at }}</p>
    </div>
    
    <div class="stats">
        <strong>Total Profiles: {{ profile_count }}</strong>
    </div>
    
    {% for profile in profiles %}
    <div class="profile">
        <h2>{{ profile.name or 'Unknown Name' }}</h2>
        <p class="url">{{ profile.url }}</p>
        
        {% if profile.headline %}
        <p><strong>Headline:</strong> {{ profile.headline }}</p>
        {% endif %}
        
        {% if profile.location %}
        <p><strong>Location:</strong> {{ profile.location }}</p>
        {% endif %}
        
        {% if profile.about %}
        <h3>About</h3>
        <p>{{ profile.about }}</p>
        {% endif %}
        
        {% if profile.experience %}
        <h3>Experience</h3>
        <ul>
        {% for exp in profile.experience %}
            <li>{{ exp }}</li>
        {% endfor %}
        </ul>
        {% endif %}
        
        {% if profile.education %}
        <h3>Education</h3>
        <ul>
        {% for edu in profile.education %}
            <li>{{ edu }}</li>
        {% endfor %}
        </ul>
        {% endif %}
        
        {% if profile.skills %}
        <h3>Skills</h3>
        <p>{{ profile.skills | join(', ') }}</p>
        {% endif %}
        
        {% if profile.quality_report %}
        <div class="quality">
            <h3>Data Quality Report</h3>
            <p><strong>Overall Score:</strong> {{ "%.1f%%" | format(profile.quality_report.overall_score * 100) }}</p>
            <p><strong>Completeness:</strong> {{ "%.1f%%" | format(profile.quality_report.completeness_score * 100) }}</p>
            <p><strong>Issues:</strong> {{ profile.quality_report.issues_count }}</p>
        </div>
        {% endif %}
        
        <p><small>Scraped at: {{ profile.scraped_at }}</small></p>
    </div>
    {% endfor %}
</body>
</html>
        """
        
        template = Template(html_template)
        return template.render(
            profiles=data_list,
            profile_count=len(data_list),
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            **kwargs
        )
    
    def batch_export(self, data_list: List[Dict[str, Any]], output_dir: str, 
                    formats: List[str] = None, base_name: str = "linkedin_profiles") -> Dict[str, bool]:
        """
        Export data in multiple formats
        
        Args:
            data_list: List of profile data
            output_dir: Output directory
            formats: List of formats to export (default: all supported)
            base_name: Base filename (without extension)
            
        Returns:
            Dictionary mapping format to success status
        """
        if formats is None:
            formats = [OutputFormat.JSON, OutputFormat.CSV, OutputFormat.EXCEL, 
                      OutputFormat.XML, OutputFormat.HTML]
        
        results = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for format_type in formats:
            extension_map = {
                OutputFormat.JSON: 'json',
                OutputFormat.CSV: 'csv',
                OutputFormat.EXCEL: 'xlsx',
                OutputFormat.XML: 'xml',
                OutputFormat.HTML: 'html',
                OutputFormat.YAML: 'yaml'
            }
            
            extension = extension_map.get(format_type, format_type)
            filename = f"{base_name}_{timestamp}.{extension}"
            output_path = os.path.join(output_dir, filename)
            
            success = self.save_data(data_list, output_path, format_type)
            results[format_type] = success
            
            if success:
                logger.info(f"Successfully exported {format_type} to {output_path}")
            else:
                logger.error(f"Failed to export {format_type}")
        
        return results 