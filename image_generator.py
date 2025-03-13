import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import os

def setup_stable_diffusion():
    """Initialize and return the Stable Diffusion pipeline"""
    model_id = "CompVis/stable-diffusion-v1-4"
    
    # Check if GPU is available
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    # Initialize the pipeline
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float32
    )
    pipe = pipe.to(device)
    
    return pipe

def generate_recipe_image(prompt, output_path):
    """Generate an image based on the recipe prompt"""
    try:
        print("Generating image...")
        pipe = setup_stable_diffusion()
        
        # Generate the image
        image = pipe(
            prompt,
            num_inference_steps=20,
            guidance_scale=7.5,
        ).images[0]
        
        # Save the image
        image.save(output_path)
        print("Image generated successfully!")
        return output_path
        
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    prompt = "A delicious plate of spaghetti carbonara, food photography, high resolution"
    output_path = "generated_recipe.png"
    generate_recipe_image(prompt, output_path)