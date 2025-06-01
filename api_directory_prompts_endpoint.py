# This is a temporary file to document the new API endpoint needed
# It should be added to src/api/router.py before the toggle endpoint

@router.get("/directories/{directory_path:path}/prompts", response_model=List[Dict])
async def get_prompts_by_directory(directory_path: str, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Get all prompts in a specific directory."""
    logger.info(f"Getting prompts for directory: {directory_path}")
    try:
        # Get prompts by directory from the service
        prompts = [prompt for prompt in prompt_service.prompts.values() if prompt.directory == directory_path]
        
        # Calculate display names if needed
        prompt_service.calculate_and_cache_display_names()
        
        # Add display names and directory info
        result = []
        for prompt in prompts:
            prompt_dict = prompt.model_dump()
            # Calculate display name
            prompt_dict["display_name"] = prompt.display_name or prompt.name or prompt.id
            prompt_dict["directory_name"] = get_directory_name(prompt.directory, prompt_service)
            result.append(prompt_dict)
        
        logger.info(f"Found {len(result)} prompts in directory {directory_path}")
        return result
        
    except Exception as e:
        logger.opt(exception=True).error(f"Error getting prompts for directory {directory_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting prompts for directory: {str(e)}")
