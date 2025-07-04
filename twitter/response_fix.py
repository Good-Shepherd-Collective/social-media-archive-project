import re

def fix_webhook_bot():
    with open('webhook_bot.py', 'r') as f:
        content = f.read()
    
    # Fix the response formatting section
    old_response_section = '''            # Success message
            success_message = f"""
✅ **{platform.title()} Content Archived!**

👤 **Author:** {author}
🆔 **Post ID:** {post_id}
📝 **Content:** {text_preview}
{media_info}
{hashtag_info}

🌐 **View:** {post_data.get('url', 'N/A')}
📊 **JSON:** https://ov-ab103a.infomaniak.ch/data/tweet_{post_id}.json

🎯 **Status:** Successfully archived with user attribution!
"""
            
            await processing_msg.edit_text(success_message, parse_mode='Markdown', disable_web_page_preview=True)'''
    
    new_response_section = '''            # Success message with safe formatting
            try:
                # Escape special characters for Markdown
                safe_author = re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\\\\1', str(author))
                safe_post_id = re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\\\\1', str(post_id))
                safe_text = re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\\\\1', str(text_preview))
                
                success_message = f"""✅ **{platform.title()} Content Archived!**

👤 **Author:** {safe_author}
🆔 **Post ID:** {safe_post_id}
📝 **Content:** {safe_text}
{media_info}
{hashtag_info}

🌐 **View:** {post_data.get('url', 'N/A')}

🎯 **Status:** Successfully archived with user attribution!"""
                
                await processing_msg.edit_text(success_message, parse_mode='Markdown', disable_web_page_preview=True)
            except Exception as format_error:
                # Fallback to plain text if Markdown fails
                simple_message = f"✅ {platform.title()} content archived successfully!\\n\\nAuthor: {author}\\nPost ID: {post_id}\\nContent: {text_preview[:100]}..."
                await processing_msg.edit_text(simple_message)'''
    
    # Replace the problematic section
    content = content.replace(old_response_section, new_response_section)
    
    with open('webhook_bot.py', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    fix_webhook_bot()
    print("✅ Fixed webhook bot response formatting")
