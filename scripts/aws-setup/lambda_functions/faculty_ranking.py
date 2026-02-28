import json
from typing import List, Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Ranks faculty members based on expertise alignment with grant requirements.
    
    Uses semantic similarity and keyword matching to calculate match scores.
    """
    try:
        # Parse input from Bedrock Agent
        # Bedrock sends action group requests in a specific format
        if 'actionGroup' in event:
            # Extract parameters from Bedrock Agent format
            parameters = event.get('parameters', [])
            body = {}
            for param in parameters:
                body[param['name']] = param['value']
        else:
            # Direct invocation format
            body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        
        faculty_list = body.get('facultyList', [])
        grant_requirements = body.get('grantRequirements', '')
        user_expertise = body.get('userExpertise', [])
        
        # Handle JSON string inputs
        if isinstance(faculty_list, str):
            faculty_list = json.loads(faculty_list)
        if isinstance(user_expertise, str):
            user_expertise = json.loads(user_expertise)
        
        # Calculate match scores
        ranked_faculty = []
        for faculty in faculty_list:
            score = calculate_match_score(
                faculty.get('expertise', ''),
                grant_requirements,
                user_expertise
            )
            
            ranked_faculty.append({
                'name': faculty['name'],
                'department': faculty['department'],
                'expertise': faculty['expertise'],
                'imageUrl': faculty.get('imageUrl', ''),
                'bio': faculty.get('bio'),
                'matchScore': score,
                'matchReason': generate_match_reason(faculty, grant_requirements, score)
            })
        
        # Sort by match score descending
        ranked_faculty.sort(key=lambda x: x['matchScore'], reverse=True)
        
        # Return in Bedrock Agent format
        response_body = {
            'rankedFaculty': ranked_faculty
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

def calculate_match_score(
    faculty_expertise: str,
    grant_requirements: str,
    user_expertise: List[str]
) -> float:
    """
    Calculate match score (0-100) based on:
    1. Keyword overlap with grant requirements
    2. Complementary expertise to user
    3. Expertise breadth
    """
    score = 0.0
    
    # Keyword matching with grant requirements (40 points)
    grant_keywords = set(grant_requirements.lower().split())
    faculty_keywords = set(faculty_expertise.lower().split())
    overlap = len(grant_keywords & faculty_keywords)
    score += min(40, overlap * 5)
    
    # Complementary expertise (40 points)
    user_keywords = set(' '.join(user_expertise).lower().split())
    complementary = len(faculty_keywords - user_keywords)
    score += min(40, complementary * 4)
    
    # Expertise breadth (20 points)
    breadth = len(faculty_keywords)
    score += min(20, breadth * 2)
    
    return min(100, score)

def generate_match_reason(
    faculty: Dict[str, Any],
    grant_requirements: str,
    score: float
) -> str:
    """Generate human-readable match justification."""
    if score >= 80:
        return f"Excellent expertise alignment in {faculty['expertise']} with grant requirements"
    elif score >= 60:
        return f"Strong complementary expertise in {faculty['expertise']}"
    else:
        return f"Relevant background in {faculty['expertise']}"
