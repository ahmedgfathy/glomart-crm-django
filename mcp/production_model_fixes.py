"""
Production fixes for properties/models.py
Replace the existing get_all_image_urls and get_image_url methods with these versions
"""

    def get_all_image_urls(self):
        """Extract all image URLs from the JSON data"""
        import json
        import re
        from django.conf import settings
        
        if not self.primary_image:
            return ['/static/images/property-placeholder.svg']
        
        try:
            # If it's a JSON array with image objects
            if self.primary_image.startswith('['):
                image_array = json.loads(self.primary_image)
                if image_array and len(image_array) > 0:
                    urls = []
                    for img in image_array:
                        # Return the original cloud URL if available and convert path
                        if 'originalUrl' in img:
                            original_url = img['originalUrl']
                            if original_url.startswith('/property-images/'):
                                # For production, use /public/ path for nginx serving
                                urls.append(original_url.replace('/property-images/', '/public/properties/images/'))
                            elif original_url.startswith('/properties/'):
                                # For production, use /public/ path
                                urls.append('/public' + original_url)
                            else:
                                urls.append(original_url)
                        # Fallback to fileUrl if available - convert to /public/ path for production
                        elif 'fileUrl' in img:
                            file_url = img['fileUrl']
                            # Convert /properties/ or /property-images/ to /public/properties/images/ for nginx serving
                            if file_url.startswith('/properties/'):
                                urls.append('/public' + file_url)
                            elif file_url.startswith('/property-images/'):
                                urls.append(file_url.replace('/property-images/', '/public/properties/images/'))
                            else:
                                urls.append(file_url)
                    return urls if urls else ['/static/images/property-placeholder.svg']
            # If it's just a direct URL string
            elif self.primary_image.startswith('http'):
                return [self.primary_image]
        except (json.JSONDecodeError, KeyError, IndexError):
            # If JSON parsing fails, try to extract fileUrl using regex
            file_url_matches = re.findall(r'"fileUrl":"([^"]+)"', self.primary_image)
            if file_url_matches:
                urls = []
                for file_url in file_url_matches:
                    if file_url.startswith('/property-images/'):
                        urls.append(file_url.replace('/property-images/', '/public/properties/images/'))
                    elif file_url.startswith('/properties/'):
                        urls.append('/public' + file_url)
                    else:
                        urls.append(file_url)
                return urls if urls else ['/static/images/property-placeholder.svg']
        
        # Fallback to placeholder
        return ['/static/images/property-placeholder.svg']

    def get_image_url(self):
        """Extract the primary image URL from the JSON data"""
        import json
        import re
        
        if not self.primary_image:
            return '/static/images/property-placeholder.svg'
        
        try:
            # If it's a JSON array with image objects
            if self.primary_image.startswith('['):
                image_array = json.loads(self.primary_image)
                if image_array and len(image_array) > 0:
                    first_image = image_array[0]
                    # Return the original cloud URL if available and convert path
                    if 'originalUrl' in first_image:
                        original_url = first_image['originalUrl']
                        if original_url.startswith('/property-images/'):
                            return original_url.replace('/property-images/', '/public/properties/images/')
                        elif original_url.startswith('/properties/'):
                            return '/public' + original_url
                        return original_url
                    # Fallback to fileUrl if available - convert to /public/ path
                    elif 'fileUrl' in first_image:
                        file_url = first_image['fileUrl']
                        if file_url.startswith('/properties/'):
                            return '/public' + file_url
                        elif file_url.startswith('/property-images/'):
                            return file_url.replace('/property-images/', '/public/properties/images/')
                        return file_url
            # If it's just a direct URL string
            elif self.primary_image.startswith('http'):
                return self.primary_image
        except (json.JSONDecodeError, KeyError, IndexError):
            # If JSON parsing fails, try to extract fileUrl using regex
            file_url_matches = re.findall(r'"fileUrl":"([^"]+)"', self.primary_image)
            if file_url_matches:
                file_url = file_url_matches[0]
                if file_url.startswith('/property-images/'):
                    return file_url.replace('/property-images/', '/public/properties/images/')
                elif file_url.startswith('/properties/'):
                    return '/public' + file_url
                return file_url
        
        # Fallback to placeholder
        return '/static/images/property-placeholder.svg' 
