require 'sinatra'
require 'erb'
require 'fileutils'

TEMPLATE_DIR = 'templates'
FileUtils.mkdir_p(TEMPLATE_DIR)

set :bind, '0.0.0.0'
set :port, 8000
set :show_exceptions, false

get '/' do
  templates = Dir.glob(File.join(TEMPLATE_DIR, '*.erb')).map { |f| File.basename(f) }

  content_type 'text/html'
  <<~HTML
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Template Renderer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }

      :root {
        --md-primary: #6750A4;
        --md-on-primary: #FFFFFF;
        --md-primary-container: #EADDFF;
        --md-on-primary-container: #21005D;
        --md-secondary: #625B71;
        --md-secondary-container: #E8DEF8;
        --md-surface: #FFFBFE;
        --md-surface-variant: #E7E0EC;
        --md-on-surface: #1C1B1F;
        --md-on-surface-variant: #49454F;
        --md-outline: #79747E;
        --md-outline-variant: #CAC4D0;
      }

      body {
        min-height: 100vh;
        background: var(--md-surface);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--md-on-surface);
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 24px;
      }

      .container {
        background: var(--md-surface);
        border-radius: 28px;
        padding: 48px;
        max-width: 520px;
        width: 100%;
        box-shadow:
          0 2px 6px 2px rgba(0, 0, 0, 0.04),
          0 1px 2px rgba(0, 0, 0, 0.06);
        border: 1px solid var(--md-outline-variant);
      }

      .logo {
        width: 48px;
        height: 48px;
        background: var(--md-primary-container);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 24px;
      }

      .logo svg {
        width: 28px;
        height: 28px;
        fill: var(--md-on-primary-container);
      }

      h1 {
        color: var(--md-on-surface);
        text-align: center;
        margin-bottom: 8px;
        font-size: 1.75rem;
        font-weight: 600;
        letter-spacing: -0.5px;
      }

      .subtitle {
        color: var(--md-on-surface-variant);
        text-align: center;
        margin-bottom: 32px;
        font-size: 0.875rem;
        font-weight: 400;
      }

      form {
        display: flex;
        flex-direction: column;
        gap: 24px;
      }

      .input-group {
        position: relative;
      }

      .input-group label {
        position: absolute;
        left: 16px;
        top: -8px;
        background: var(--md-surface);
        padding: 0 4px;
        font-size: 0.75rem;
        color: var(--md-primary);
        font-weight: 500;
      }

      input[type="text"] {
        width: 100%;
        padding: 16px;
        border: 1px solid var(--md-outline);
        border-radius: 4px;
        background: transparent;
        color: var(--md-on-surface);
        font-size: 1rem;
        font-family: inherit;
        transition: all 0.2s ease;
      }

      input[type="text"]:hover {
        border-color: var(--md-on-surface);
      }

      input[type="text"]:focus {
        outline: none;
        border-color: var(--md-primary);
        border-width: 2px;
        padding: 15px;
      }

      input[type="text"]::placeholder {
        color: var(--md-on-surface-variant);
      }

      button {
        padding: 0 24px;
        height: 40px;
        background: var(--md-primary);
        border: none;
        border-radius: 20px;
        color: var(--md-on-primary);
        font-size: 0.875rem;
        font-weight: 500;
        font-family: inherit;
        cursor: pointer;
        transition: all 0.2s ease;
        letter-spacing: 0.1px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        align-self: flex-end;
      }

      button:hover {
        box-shadow: 0 1px 3px 1px rgba(0, 0, 0, 0.15), 0 1px 2px rgba(0, 0, 0, 0.3);
      }

      button:active {
        background: #7965AF;
      }

      button svg {
        width: 18px;
        height: 18px;
        fill: currentColor;
      }

      .templates-section {
        margin-top: 32px;
        padding-top: 24px;
        border-top: 1px solid var(--md-outline-variant);
      }

      .templates-section h2 {
        color: var(--md-on-surface-variant);
        font-size: 0.75rem;
        font-weight: 500;
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .template-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .template-item {
        padding: 8px 16px;
        background: var(--md-surface-variant);
        border-radius: 8px;
        color: var(--md-on-surface-variant);
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: none;
      }

      .template-item:hover {
        background: var(--md-secondary-container);
        color: var(--md-on-primary-container);
      }

      .template-item:active {
        background: var(--md-primary-container);
      }

      .empty-state {
        text-align: center;
        padding: 24px;
        color: var(--md-on-surface-variant);
        font-size: 0.875rem;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="logo">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20ZM9 13V19H7V13H9ZM15 15V19H17V15H15ZM11 11V19H13V11H11Z"/>
        </svg>
      </div>

      <h1>Template Renderer</h1>
      <p class="subtitle">Enter a template path to render your ERB files</p>

      <form action="/render" method="post">
        <div class="input-group">
          <label for="template">Template Path</label>
          <input type="text" id="template" name="template" placeholder="e.g., cyberpunk.erb" required>
        </div>
        <button type="submit">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 5V19L19 12L8 5Z"/>
          </svg>
          Render
        </button>
      </form>

      <div class="templates-section">
        <h2>Available Templates</h2>
        <div class="template-list">
          #{templates.empty? ? "<p class='empty-state'>No templates found</p>" : templates.map { |t| "<span class='template-item' onclick=\"document.getElementById('template').value='#{t}'\">#{t}</span>" }.join}
        </div>
      </div>
    </div>
  </body>
  </html>
  HTML
end

post '/render' do
  template_name = params[:template]

  if template_name.nil? || template_name.empty?
    status 400
    return "Missing template name"
  end

  template_path = File.join(TEMPLATE_DIR, template_name)

  begin
    template_content = File.read(template_path)
    renderer = ERB.new(template_content)
    output = renderer.result(binding)

    content_type 'text/html'
    return output

  rescue Errno::ENOENT
    status 404
    return "Template not found"
  rescue => _
    status 500
    return "Render Error"
  end
end