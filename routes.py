import os
import uuid
from flask import render_template, request, redirect, url_for, flash, send_file, jsonify, abort
from werkzeug.utils import secure_filename
from app import app, db
from models import Document, DocumentStatus
from utils import convert_url_to_pdf, convert_epub_to_pdf, allowed_file, get_file_size_mb

@app.route('/')
def index():
    """Homepage with quick stats and recent documents"""
    total_docs = Document.query.count()
    to_read = Document.query.filter_by(status=DocumentStatus.TO_READ).count()
    in_progress = Document.query.filter_by(status=DocumentStatus.IN_PROGRESS).count()
    completed = Document.query.filter_by(status=DocumentStatus.COMPLETED).count()
    
    recent_docs = Document.query.order_by(Document.upload_date.desc()).limit(5).all()
    
    return render_template('index.html', 
                         total_docs=total_docs,
                         to_read=to_read,
                         in_progress=in_progress,
                         completed=completed,
                         recent_docs=recent_docs)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads (PDF and EPUB)"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Generate unique filename
                file_ext = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Save file
                file.save(file_path)
                
                # Use provided title or filename
                if not title:
                    title = file.filename.rsplit('.', 1)[0]
                
                # Handle EPUB conversion
                final_filename = unique_filename
                final_file_type = file_ext
                
                if file_ext == 'epub':
                    try:
                        pdf_filename = f"{uuid.uuid4().hex}.pdf"
                        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
                        
                        if convert_epub_to_pdf(file_path, pdf_path):
                            # Remove original EPUB file
                            os.remove(file_path)
                            final_filename = pdf_filename
                            final_file_type = 'pdf'
                            title += " (converted from EPUB)"
                        else:
                            flash('Failed to convert EPUB to PDF', 'error')
                            os.remove(file_path)
                            return redirect(request.url)
                    except Exception as e:
                        flash(f'EPUB conversion error: {str(e)}', 'error')
                        os.remove(file_path)
                        return redirect(request.url)
                
                # Get file size
                final_path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
                file_size = os.path.getsize(final_path)
                
                # Save to database
                document = Document(
                    title=title,
                    filename=final_filename,
                    original_filename=file.filename,
                    file_type=final_file_type,
                    file_size=file_size,
                    description=description
                )
                
                db.session.add(document)
                db.session.commit()
                
                flash(f'File "{title}" uploaded successfully!', 'success')
                return redirect(url_for('library'))
                
            except Exception as e:
                flash(f'Upload failed: {str(e)}', 'error')
                app.logger.error(f'Upload error: {str(e)}')
        else:
            flash('Invalid file type. Only PDF and EPUB files are allowed.', 'error')
    
    return render_template('upload.html')

@app.route('/convert-url', methods=['GET', 'POST'])
def convert_url():
    """Convert web page to PDF"""
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if not url:
            flash('Please enter a valid URL', 'error')
            return redirect(request.url)
        
        try:
            # Generate unique filename
            pdf_filename = f"{uuid.uuid4().hex}.pdf"
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            
            # Convert URL to PDF
            success, error_msg = convert_url_to_pdf(url, pdf_path)
            
            if success:
                # Use provided title or extract from URL
                if not title:
                    title = f"Web Page - {url}"
                
                # Get file size
                file_size = os.path.getsize(pdf_path)
                
                # Save to database
                document = Document(
                    title=title,
                    filename=pdf_filename,
                    original_filename=f"{title}.pdf",
                    file_type='pdf',
                    file_size=file_size,
                    source_url=url,
                    description=description
                )
                
                db.session.add(document)
                db.session.commit()
                
                flash(f'Web page "{title}" converted to PDF successfully!', 'success')
                return redirect(url_for('library'))
            else:
                flash(f'Conversion failed: {error_msg}', 'error')
                
        except Exception as e:
            flash(f'Conversion error: {str(e)}', 'error')
            app.logger.error(f'URL conversion error: {str(e)}')
    
    return render_template('convert_url.html')

@app.route('/library')
def library():
    """Display all documents in the library"""
    # Get filter parameters
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    # Build query
    query = Document.query
    
    if status_filter:
        try:
            status_enum = DocumentStatus(status_filter)
            query = query.filter_by(status=status_enum)
        except ValueError:
            pass
    
    if search_query:
        query = query.filter(Document.title.contains(search_query))
    
    documents = query.order_by(Document.upload_date.desc()).all()
    
    return render_template('library.html', 
                         documents=documents,
                         current_status=status_filter,
                         search_query=search_query)

@app.route('/view/<filename>')
def view_pdf(filename):
    """View PDF in browser"""
    document = Document.query.filter_by(filename=filename).first()
    if not document:
        abort(404)
    
    # Increment view count
    document.view_count += 1
    db.session.commit()
    
    return render_template('view_pdf.html', document=document)

@app.route('/download/<filename>')
def download_file(filename):
    """Download file"""
    document = Document.query.filter_by(filename=filename).first()
    if not document:
        abort(404)
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path, as_attachment=True, 
                    download_name=document.original_filename)

@app.route('/serve/<filename>')
def serve_file(filename):
    """Serve file for PDF viewer"""
    document = Document.query.filter_by(filename=filename).first()
    if not document:
        abort(404)
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path)

@app.route('/update-status/<int:doc_id>', methods=['POST'])
def update_status(doc_id):
    """Update document reading status"""
    document = Document.query.get_or_404(doc_id)
    new_status = request.form.get('status')
    
    try:
        document.status = DocumentStatus(new_status)
        db.session.commit()
        flash(f'Status updated to {document.get_status_display()}', 'success')
    except ValueError:
        flash('Invalid status', 'error')
    
    return redirect(url_for('library'))

@app.route('/delete/<int:doc_id>', methods=['POST'])
def delete_document(doc_id):
    """Delete document"""
    document = Document.query.get_or_404(doc_id)
    
    try:
        # Delete file from filesystem
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        db.session.delete(document)
        db.session.commit()
        
        flash(f'Document "{document.title}" deleted successfully', 'success')
    except Exception as e:
        flash(f'Delete failed: {str(e)}', 'error')
        app.logger.error(f'Delete error: {str(e)}')
    
    return redirect(url_for('library'))

@app.route('/gpa-calculator')
def gpa_calculator():
    """GPA Calculator page"""
    return render_template('gpa_calculator.html')

@app.route('/calculate-gpa', methods=['POST'])
def calculate_gpa():
    """Calculate GPA from submitted courses"""
    try:
        courses_data = request.get_json()
        courses = courses_data.get('courses', [])
        
        if not courses:
            return jsonify({'error': 'No courses provided'}), 400
        
        # Grade point mapping
        grade_points = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'F': 0.0
        }
        
        total_credit_hours = 0
        total_quality_points = 0
        
        for course in courses:
            credit_hours = float(course.get('credit_hours', 0))
            grade = course.get('grade', '').upper()
            
            if grade in grade_points:
                total_credit_hours += credit_hours
                total_quality_points += credit_hours * grade_points[grade]
        
        if total_credit_hours == 0:
            return jsonify({'error': 'No valid courses with credit hours'}), 400
        
        gpa = total_quality_points / total_credit_hours
        
        return jsonify({
            'gpa': round(gpa, 2),
            'total_credit_hours': total_credit_hours,
            'total_courses': len(courses)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html'), 404

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 50MB.', 'error')
    return redirect(request.url)
