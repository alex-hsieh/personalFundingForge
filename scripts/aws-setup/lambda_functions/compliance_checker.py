import json
from typing import List, Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validates compliance checklist items against FSU policies.
    
    Assigns status indicators (green, yellow, red) based on task requirements.
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
        
        checklist_items = body.get('checklistItems', [])
        grant_type = body.get('grantType', 'general')
        
        # Handle JSON string input
        if isinstance(checklist_items, str):
            checklist_items = json.loads(checklist_items)
        
        # Validate each checklist item
        validated_checklist = []
        for item in checklist_items:
            validated_item = validate_task(item, grant_type)
            validated_checklist.append(validated_item)
        
        # Check for missing critical tasks
        missing_tasks = check_missing_critical_tasks(validated_checklist, grant_type)
        for task in missing_tasks:
            validated_checklist.append(task)
        
        response_body = {
            'validatedChecklist': validated_checklist
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

def validate_task(item: Dict[str, Any], grant_type: str) -> Dict[str, Any]:
    """
    Validate a single compliance task and assign status.
    """
    task = item.get('task', '')
    category = item.get('category', 'Policy')
    
    # Define critical keywords for each category
    critical_keywords = {
        'RAMP': ['submit', 'approval', 'deadline'],
        'COI': ['disclosure', 'conflict', 'financial'],
        'IRB': ['human subjects', 'protocol', 'approval'],
        'Policy': ['required', 'mandatory', 'must']
    }
    
    # Assign status based on task content and category
    task_lower = task.lower()
    status = 'green'  # Default to green
    notes = ''
    
    # Check for critical keywords
    if category in critical_keywords:
        keywords = critical_keywords[category]
        if any(keyword in task_lower for keyword in keywords):
            # Critical task - needs attention
            if 'deadline' in task_lower or 'submit' in task_lower:
                status = 'yellow'
                notes = 'Time-sensitive requirement - plan ahead'
            elif 'approval' in task_lower or 'required' in task_lower:
                status = 'yellow'
                notes = 'Requires action before submission'
    
    # Special handling for IRB
    if category == 'IRB':
        if 'human subjects' in task_lower:
            status = 'red'
            notes = 'IRB approval required before data collection'
    
    # Special handling for COI
    if category == 'COI':
        if 'disclosure' in task_lower:
            status = 'yellow'
            notes = 'Annual disclosure required'
    
    return {
        'task': task,
        'category': category,
        'status': status,
        'notes': notes
    }

def check_missing_critical_tasks(
    validated_checklist: List[Dict[str, Any]],
    grant_type: str
) -> List[Dict[str, Any]]:
    """
    Check for missing critical compliance tasks.
    """
    missing_tasks = []
    
    # Define required categories
    required_categories = {'RAMP', 'COI'}
    existing_categories = {item['category'] for item in validated_checklist}
    
    # Add missing RAMP task
    if 'RAMP' not in existing_categories:
        missing_tasks.append({
            'task': 'Submit proposal through RAMP system',
            'category': 'RAMP',
            'status': 'red',
            'notes': 'Critical: All proposals must be submitted through RAMP'
        })
    
    # Add missing COI task
    if 'COI' not in existing_categories:
        missing_tasks.append({
            'task': 'Complete Conflict of Interest disclosure',
            'category': 'COI',
            'status': 'yellow',
            'notes': 'Required: Annual COI disclosure must be current'
        })
    
    return missing_tasks
