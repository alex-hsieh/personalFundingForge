import json
import re
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Formats proposal drafts according to grant templates.
    
    Applies proper structure, section headers, and formatting.
    """
    try:
        # Parse input from Bedrock Agent
        if 'actionGroup' in event:
            parameters = event.get('parameters', [])
            body = {}
            for param in parameters:
                body[param['name']] = param['value']
        else:
            body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        
        proposal_text = body.get('proposalText', '')
        grant_name = body.get('grantName', 'Grant Proposal')
        format_style = body.get('formatStyle', 'standard')
        
        # Format the proposal
        formatted_proposal = format_proposal(proposal_text, grant_name, format_style)
        
        response_body = {
            'formattedProposal': formatted_proposal
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_body),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

def format_proposal(proposal_text: str, grant_name: str, format_style: str) -> str:
    """
    Format proposal with proper structure and sections.
    """
    # Clean up the text
    proposal_text = clean_paragraph(proposal_text)
    
    # Define section structure
    sections = {
        'Executive Summary': extract_section(proposal_text, 'executive summary', 'principal investigator'),
        'Principal Investigator Qualifications': extract_section(proposal_text, 'principal investigator', 'collaborative team'),
        'Collaborative Team': extract_section(proposal_text, 'collaborative team', 'compliance'),
        'Compliance and Requirements': extract_section(proposal_text, 'compliance', 'conclusion'),
        'Conclusion': extract_section(proposal_text, 'conclusion', None)
    }
    
    # Build formatted proposal
    formatted_parts = []
    
    # Title
    formatted_parts.append(f"# {grant_name}")
    formatted_parts.append("")
    formatted_parts.append("---")
    formatted_parts.append("")
    
    # Sections
    for section_title, section_content in sections.items():
        if section_content:
            formatted_parts.append(f"## {section_title}")
            formatted_parts.append("")
            formatted_parts.append(section_content)
            formatted_parts.append("")
    
    # If no sections found, use original text with basic formatting
    if not any(sections.values()):
        formatted_parts.append(proposal_text)
    
    return '\n'.join(formatted_parts)

def extract_section(text: str, start_marker: str, end_marker: str = None) -> str:
    """
    Extract a section from the proposal text.
    """
    text_lower = text.lower()
    
    # Find start position
    start_pos = text_lower.find(start_marker)
    if start_pos == -1:
        return ''
    
    # Find end position
    if end_marker:
        end_pos = text_lower.find(end_marker, start_pos + len(start_marker))
        if end_pos == -1:
            end_pos = len(text)
    else:
        end_pos = len(text)
    
    # Extract section
    section = text[start_pos:end_pos]
    
    # Remove the section header if it's at the start
    section = re.sub(r'^[^\n]*' + re.escape(start_marker) + r'[^\n]*\n', '', section, flags=re.IGNORECASE)
    
    return section.strip()

def clean_paragraph(text: str) -> str:
    """
    Clean up paragraph formatting.
    """
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Ensure proper spacing after periods
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def add_section_numbers(text: str) -> str:
    """
    Add section numbering to headers.
    """
    lines = text.split('\n')
    section_num = 1
    subsection_num = 1
    
    formatted_lines = []
    for line in lines:
        if line.startswith('## '):
            formatted_lines.append(f"## {section_num}. {line[3:]}")
            section_num += 1
            subsection_num = 1
        elif line.startswith('### '):
            formatted_lines.append(f"### {section_num-1}.{subsection_num}. {line[4:]}")
            subsection_num += 1
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)
