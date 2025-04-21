FROM php:apache

# Enable Apache headers and rewrite modules for CORS
RUN a2enmod headers rewrite

# Copy CORS configuration to Apache
COPY apache-cors.conf /etc/apache2/conf-available/cors.conf

# Enable CORS configuration
RUN a2enconf cors

# Restart Apache when container starts
CMD ["apache2-foreground"]
