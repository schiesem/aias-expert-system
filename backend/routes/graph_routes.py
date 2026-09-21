# routes/graph_routes.py

"""
Graph Visualization Routes

API endpoints for serving ontology graph visualizations.
"""

from flask import Blueprint, jsonify, send_file
from app_globals import get_current_world_id, get_world_manager
import os
import asyncio
from playwright.async_api import async_playwright
import tempfile

graph_viz_bp = Blueprint("graph_viz_bp", __name__, url_prefix="/api/graph")


@graph_viz_bp.route("/check", methods=["GET"])
def check_graphs():
    """
    Check which graph visualizations are available for the current world.

    Returns:
        JSON: {
            success: bool,
            instance_exists: bool,
            inferred_exists: bool
        }
    """
    try:
        world_mgr = get_world_manager()
        world_id = get_current_world_id()

        # Get world directory
        world_dir = world_mgr._get_world_dir(world_id)

        # Check if graph HTML files exist in the world folder
        instance_graph_path = os.path.join(world_dir, "ontology_graph_instance.html")
        inferred_graph_path = os.path.join(world_dir, "ontology_graph_inferred.html")

        instance_exists = os.path.exists(instance_graph_path)
        inferred_exists = os.path.exists(inferred_graph_path)

        return jsonify({
            "success": True,
            "instance_exists": instance_exists,
            "inferred_exists": inferred_exists
        }), 200

    except Exception as e:
        print(f"❌ Error checking graphs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@graph_viz_bp.route("/instance", methods=["GET"])
def get_instance_graph():
    """
    Serve the instance graph visualization HTML for the current world.

    Returns:
        HTML file
    """
    try:
        world_mgr = get_world_manager()
        world_id = get_current_world_id()
        world_dir = world_mgr._get_world_dir(world_id)

        graph_path = os.path.join(world_dir, "ontology_graph_instance.html")

        if not os.path.exists(graph_path):
            return jsonify({
                "success": False,
                "error": "Instance graph not found. Sync the model first."
            }), 404

        return send_file(
            graph_path,
            mimetype='text/html',
            as_attachment=False
        )

    except Exception as e:
        print(f"❌ Error serving instance graph: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@graph_viz_bp.route("/inferred", methods=["GET"])
def get_inferred_graph():
    """
    Serve the inferred graph visualization HTML for the current world.

    Returns:
        HTML file
    """
    try:
        world_mgr = get_world_manager()
        world_id = get_current_world_id()
        world_dir = world_mgr._get_world_dir(world_id)

        graph_path = os.path.join(world_dir, "ontology_graph_inferred.html")

        if not os.path.exists(graph_path):
            return jsonify({
                "success": False,
                "error": "Inferred graph not found. Run reasoning first."
            }), 404

        return send_file(
            graph_path,
            mimetype='text/html',
            as_attachment=False
        )

    except Exception as e:
        print(f"❌ Error serving inferred graph: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@graph_viz_bp.route("/export-pdf/<graph_type>", methods=["GET"])
def export_graph_as_pdf(graph_type):
    """
    Export the graph visualization as PDF using Playwright.

    Args:
        graph_type: Either "instance" or "inferred"

    Returns:
        PDF file for download
    """
    try:
        world_mgr = get_world_manager()
        world_id = get_current_world_id()
        world_dir = world_mgr._get_world_dir(world_id)

        # Determine which graph to export
        if graph_type == "instance":
            graph_path = os.path.join(world_dir, "ontology_graph_instance.html")
        elif graph_type == "inferred":
            graph_path = os.path.join(world_dir, "ontology_graph_inferred.html")
        else:
            return jsonify({
                "success": False,
                "error": "Invalid graph type. Must be 'instance' or 'inferred'."
            }), 400

        if not os.path.exists(graph_path):
            return jsonify({
                "success": False,
                "error": f"{graph_type.capitalize()} graph not found. Generate the graph first."
            }), 404

        # Create temporary PDF file
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf.close()

        # Run async playwright function
        asyncio.run(generate_pdf_from_html(graph_path, temp_pdf.name))

        # Send PDF file
        return send_file(
            temp_pdf.name,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ontology_graph_{graph_type}.pdf'
        )

    except Exception as e:
        print(f"❌ Error exporting graph as PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


async def generate_pdf_from_html(html_path: str, pdf_path: str):
    """
    Generate PDF from HTML file using Playwright.
    Takes a high-resolution screenshot and converts it to PDF.

    Args:
        html_path: Path to the HTML file
        pdf_path: Path where PDF should be saved
    """
    from PIL import Image
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas as pdf_canvas

    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)

        # Set viewport to high resolution for better quality
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})

        # Load the HTML file
        await page.goto(f'file:///{html_path.replace(os.sep, "/")}')

        # Wait for the vis-network canvas to be rendered
        try:
            # Wait for the canvas element to appear (max 10 seconds)
            await page.wait_for_selector('#mynetwork canvas', timeout=10000)
            print('✅ Canvas found, waiting for graph to stabilize...')

            # Additional wait for graph stabilization (vis-network physics)
            await page.wait_for_timeout(3000)

        except Exception as e:
            print(f'⚠️ Warning: Could not find canvas element: {e}')
            # Continue anyway, maybe the graph is there

        # Take a high-resolution screenshot of the graph container
        graph_element = await page.query_selector('#mynetwork')

        if graph_element:
            # Screenshot only the graph container (not the buttons)
            screenshot_bytes = await graph_element.screenshot(type='png')
        else:
            # Fallback: screenshot the whole page
            screenshot_bytes = await page.screenshot(full_page=True, type='png')

        await browser.close()

        # Save screenshot to temporary file
        temp_png = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_png.write(screenshot_bytes)
        temp_png.close()

        # Convert screenshot to PDF using ReportLab
        try:
            # Open image with PIL
            img = Image.open(temp_png.name)
            img_width, img_height = img.size

            # Create PDF in landscape A4
            page_width, page_height = landscape(A4)

            # Calculate scaling to fit on A4
            scale = min((page_width - 20) / img_width, (page_height - 20) / img_height)
            scaled_width = img_width * scale
            scaled_height = img_height * scale

            # Center the image on the page
            x_offset = (page_width - scaled_width) / 2
            y_offset = (page_height - scaled_height) / 2

            # Create PDF
            c = pdf_canvas.Canvas(pdf_path, pagesize=landscape(A4))
            c.drawImage(temp_png.name, x_offset, y_offset,
                       width=scaled_width, height=scaled_height,
                       preserveAspectRatio=True)
            c.save()

            # Close the image to release file handle (important on Windows)
            img.close()

            # Clean up temporary PNG
            try:
                os.remove(temp_png.name)
            except PermissionError:
                # On Windows, file might still be locked, just log and continue
                print(f'⚠️ Warning: Could not delete temporary file {temp_png.name}')

            print(f'✅ PDF generated successfully: {pdf_path}')
        except Exception as e:
            print(f'❌ Error converting screenshot to PDF: {e}')
            # Clean up temporary PNG on error
            try:
                if os.path.exists(temp_png.name):
                    os.remove(temp_png.name)
            except PermissionError:
                pass  # Ignore if we can't delete
            raise
