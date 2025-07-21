<!-- Vienna landmark background image -->
![Vienna Landmark](assets/media/vienna1.jpg)

<!-- Wiener Linien App Section -->
<div style="background: linear-gradient(135deg, #f8faff 0%, #edf4ff 100%); border: 1px solid #d0e3ff; border-radius: 12px; padding: 2.5rem; margin: 2.5rem auto; max-width: 850px; box-shadow: 0 4px 20px rgba(0, 60, 136, 0.1); position: relative; overflow: hidden;">
  <!-- Decorativelements -->
  <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: radial-gradient(circle, rgba(0, 102, 204, 0.1) 0%, rgba(0, 102, 204, 0) 70%); border-radius: 50%;"></div>
  
  <div style="position: relative; z-index: 1;">
    <h2 style="color: #003b82; margin-top: 0; font-size: 2.2em; margin-bottom: 0.8em; position: relative; display: inline-block;">
      <span style="display: inline-block; padding-bottom: 0.3em; border-bottom: 3px solid #0066cc;">Wiener Linien Live Map</span>
      <span style="display: inline-block; background: #ffcc00; color: #003b82; font-size: 0.6em; padding: 0.3em 0.8em; border-radius: 12px; margin-left: 0.8em; font-weight: bold; vertical-align: middle;">BETA</span>
    </h2>
    
    <p style="font-size: 1.25em; line-height: 1.6; color: #2c3e50; margin-bottom: 2em;">
      <span style="display: inline-block; margin-bottom: 0.8em;">
        🚇 Explore Vienna's public transport network with our interactive map interface.
      </span>
      <span style="display: block; margin-bottom: 0.8em;">
        🚦 View all U-Bahn, tram, and bus routes across the city.
      </span>
      <span style="display: block; margin-bottom: 1.5em; font-style: italic; color: #6c757d;">
        Note: Currently in active development. Some features may be limited.
      </span>
    </p>
    
    <div style="display: flex; flex-wrap: wrap; gap: 1.2rem; justify-content: center;">
      <a href="http://localhost:3080" class="cover-button" style="background: linear-gradient(135deg, #0066cc 0%, #004d99 100%); color: white; padding: 1em 2.5em; border-radius: 8px; text-decoration: none; display: inline-flex; align-items: center; font-size: 1.15em; font-weight: 600; transition: all 0.3s ease; border: none; box-shadow: 0 4px 15px rgba(0, 102, 204, 0.3);">
        <span>Launch Mapp</span>
        <span style="margin-left: 0.8em; font-size: 1.2em;">→</span>
      </a>
      
      <a href="/PRD.md" class="cover-button" style="background: white; color: #0066cc; padding: 1em 2em; border-radius: 8px; text-decoration: none; display: inline-flex; align-items: center; font-size: 1.05em; font-weight: 500; transition: all 0.3s ease; border: 2px solid #d0e3ff; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);">
        <span>📄 Project Info</span>
      </a>
    </div>
    
    <div style="margin-top: 1.5em; font-size: 0.9em; color: #6c757d; display: flex; align-items: center; justify-content: center; gap: 0.5em;">
      <span>Running on port 3080</span>
      <span style="display: inline-block; width: 8px; height: 8px; background: #28a745; border-radius: 50%;"></span>
    </div>
  </div>
</div>

<!-- Main content container -->
<div style="text-align: center; padding: 1rem; color: #333;">
  <!-- Main heading -->
  <h1 style="font-size: 2.5em; margin: 0.5em 0.3em;">Documentation Hub</h1>
  
  <!-- Tagline -->
  <p style="font-size: 1.3em; margin-bottom: 2em;">Documentation & Resources</p>
  
  <!-- Buttons -->
  <div style="margin-top: 2em;">
    <a href="https://github.com/sandraschi/mywienerlinien" class="cover-button" style="background: #0066cc; color: white; padding: 0.8em 1.8em; border-radius: 4px; text-decoration: none; margin: 0.5em; display: inline-block; transition: all 0.3s ease; border: 2px solid #0066cc;">
      GitHub
    </a>
    <a href="#/README" class="cover-button" style="background: #0066cc; color: white; padding: 0.8em 1.8em; border-radius: 4px; text-decoration: none; margin: 0.5em; display: inline-block; transition: all 0.3s ease; border: 2px solid #0066cc;">
      Get Started
    </a>
    <a href="#/" class="cover-button" style="background: transparent; color: #0066cc; padding: 0.8em 1.8em; border-radius: 4px; text-decoration: none; margin: 0.5em; display: inline-block; transition: all 0.3s ease; border: 2px solid #0066cc;">
      Explore Documentation
    </a>
  </div>
  
  <!-- Version and attribution -->
  <div style="margin-top: 2rem; font-size: 0.9em; color: #666;">
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
