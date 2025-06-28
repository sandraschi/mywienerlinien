<!-- Vienna landmark background image -->
![Vienna Landmark](assets/media/vienna1.jpg)

<!-- Overlay with semi-transparent dark layer for better text readability -->
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.4);"></div>

<!-- Main content container -->
<div style="position: relative; z-index: 1; text-align: center; color: white; padding: 2rem; text-shadow: 1px 1px 3px rgba(0,0,0,0.8);">
  
  <!-- Logo (if available) -->
  ![Logo](/_media/logo.png)
  
  <!-- Main heading -->
  <h1 style="font-size: 3.5em; margin-bottom: 0.5em; color: #fff;">MyWienerLinien</h1>
  
  <!-- Tagline -->
  <p style="font-size: 1.5em; margin-bottom: 1.5em; color: #f0f0f0;">Documentation & Resources</p>
  
  <!-- Buttons -->
  <div style="margin-top: 2em;">
    <a href="https://github.com/sandraschi/mywienerlinien" class="cover-button" style="background: #0066cc; color: white; padding: 0.8em 1.8em; border-radius: 4px; text-decoration: none; margin: 0.5em; display: inline-block; transition: all 0.3s ease; border: 2px solid #0066cc;">
      GitHub
    </a>
    <a href="#/README" class="cover-button" style="background: #0066cc; color: white; padding: 0.8em 1.8em; border-radius: 4px; text-decoration: none; margin: 0.5em; display: inline-block; transition: all 0.3s ease; border: 2px solid #0066cc;">
      Get Started
    </a>
    <a href="#/docs/" class="cover-button" style="background: transparent; color: white; padding: 0.8em 1.8em; border-radius: 4px; text-decoration: none; margin: 0.5em; display: inline-block; transition: all 0.3s ease; border: 2px solid white;">
      Explore Documentation
    </a>
  </div>
  
  <!-- Version and attribution -->
  <div style="position: absolute; bottom: 1rem; right: 1rem; font-size: 0.8em; color: rgba(255,255,255,0.7);">
    Vienna, Austria
  </div>
</div>

<style>
  :root {
    --cover-heading-color: #333;
    --cover-button-color: #fff;
    --cover-button-bg: #0066cc;
    --cover-button-border: none;
  }
  
  .cover {
    color: #333;
  }
  
  .cover h1 {
    font-size: 3.5em;
    margin: 0.5em 0;
  }
  
  .cover .cover-main > p:last-child a {
    border-radius: 4px;
    padding: 0.6em 1.2em;
    margin: 0.5em;
    transition: all 0.3s ease;
  }
  
  .cover .cover-main > p:last-child a:first-child {
    background-color: var(--cover-button-bg);
    color: var(--cover-button-color);
    border: var(--cover-button-border);
  }
  
  .cover .cover-main > p:last-child a:first-child:hover {
    background-color: #0052a3;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  }
  
  .cover .cover-main > p:last-child a:last-child {
    background-color: transparent;
    color: var(--cover-button-bg);
    border: 1px solid var(--cover-button-bg);
  }
  
  .cover .cover-main > p:last-child a:last-child:hover {
    background-color: rgba(0, 102, 204, 0.1);
  }
  
  @media screen and (max-width: 768px) {
    .cover h1 {
      font-size: 2.5em;
    }
    
    .cover .cover-main > p:last-child a {
      display: block;
      margin: 0.5em auto;
      max-width: 200px;
    }
  }
</style>
