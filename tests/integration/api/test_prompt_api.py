import pytest
import httpx

# Base URL for the API
BASE_URL = "http://localhost:8095/api"

@pytest.mark.asyncio
async def test_get_all_prompts_returns_list():
    """
    Test that GET /api/prompts returns a 200 OK and a list (even if empty).
    Assumes the Prompt Manager server is running at BASE_URL.
    """
    async with httpx.AsyncClient(base_url=BASE_URL, follow_redirects=True) as client:
        try:
            response = await client.get("/prompts/all")
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)
            
            # Optionally, if you have known prompts or can set them up:
            # - Assert specific prompts are present or the list has a certain length
            # - For now, just checking type is a good start.
            print(f"Response from /api/prompts: {response.json()}")

        except httpx.HTTPStatusError as exc:
            pytest.fail(f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}")
        except httpx.RequestError as exc:
            pytest.fail(f"Request error occurred: {exc}")
        except Exception as exc:
            pytest.fail(f"An unexpected error occurred: {exc}")

# Add more tests here for other endpoints, e.g.:
# - Creating a prompt (POST /api/prompts)
# - Getting a specific prompt (GET /api/prompts/{prompt_id})
# - Updating a prompt (PUT /api/prompts/{prompt_id})
# - Deleting a prompt (DELETE /api/prompts/{prompt_id})

# Example of a test that might expect failure if prompt doesn't exist
# @pytest.mark.asyncio
# async def test_get_nonexistent_prompt_returns_404():
#     async with httpx.AsyncClient(base_url=BASE_URL) as client:
#         try:
#             response = await client.get("/prompts/this_prompt_does_not_exist_i_hope")
#             assert response.status_code == 404
#         except httpx.RequestError as exc:
#             pytest.fail(f"Request error occurred: {exc}") 