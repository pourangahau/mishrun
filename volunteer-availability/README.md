# Volunteer Availability Calendar

A sophisticated web application for managing volunteer availability with visual density indicators and server-side persistence.

## Features

### Core Functionality
- **Interactive Calendar Interface**: Click to select available dates
- **Month/Year Selection**: Choose any month from current year through 3 years ahead
- **Shift Type Configuration**: North only, South only, or Both North and South
- **Workload Settings**: Configure shifts per fortnight (1-10)
- **Date Restrictions**: Only Tuesday through Friday can be selected (weekends and Mondays disabled)

### Advanced Features
- **Visual Density Indicators**: See how many volunteers have selected each date
  - **North Run**: Top half of each date shows blue intensity (1-20 scale)
  - **South Run**: Bottom half of each date shows red intensity (1-20 scale)
- **Server-Side Storage**: Data persists across sessions using Flask backend
- **Overwrite Protection**: Warns users before overwriting existing availability
- **Real-Time Updates**: Calendar refreshes to show updated density after saving

### User Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Professional Styling**: Modern gradient headers and clean layout
- **Intuitive Controls**: Clear visual feedback for all interactions
- **Accessibility**: High contrast colors and readable text

## Technical Architecture

### Frontend
- **Pure HTML/CSS/JavaScript**: No external dependencies
- **ES6 Classes**: Modern JavaScript architecture
- **CSS Grid**: Responsive calendar layout
- **Fetch API**: Asynchronous server communication

### Backend
- **Python Flask**: RESTful API server
- **JSON Storage**: File-based data persistence
- **CORS Enabled**: Cross-origin resource sharing
- **Error Handling**: Comprehensive validation and error responses

## Installation and Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Backend Setup
1. Navigate to the project directory:
   ```bash
   cd volunteer-availability
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the Flask server:
   ```bash
   python app.py
   ```
   
   The server will start on `http://localhost:5000`

### Frontend Setup
1. Open `index.html` in a web browser
2. Or serve via a local web server:
   ```bash
   # Using Python's built-in server
   python -m http.server 8000
   ```
   
   Then visit `http://localhost:8000`

## Usage Guide

### Basic Usage
1. **Enter Your Information**:
   - Name (required)
   - Shift type: North only (N), South only (S), or Both (NS)
   - Workload: Number of shifts per fortnight

2. **Select Month and Year**:
   - Choose from dropdown menus
   - Click "Generate Calendar"

3. **Select Available Dates**:
   - Click on dates to toggle availability (Tuesday-Friday only)
   - Green highlighting indicates selected dates
   - Weekends and Mondays are disabled (grayed out)

4. **Save Your Availability**:
   - Click "Save Availability"
   - Confirm overwrite if you've previously saved for this month
   - Calendar updates to show your contribution to the density visualization

### Understanding Density Visualization
- **Blue Shading (Top Half)**: Number of volunteers available for North runs
- **Red Shading (Bottom Half)**: Number of volunteers available for South runs
- **Intensity Scale**: Darker colors indicate more volunteers (1-20 scale)
- **Combined Availability**: Volunteers selecting "Both" contribute to both North and South counts

### Additional Controls
- **Clear All**: Remove all selected dates
- **Select All**: Select all available dates (Tuesday-Friday only)
- **Overwrite Warning**: System prompts before replacing existing data

## API Endpoints

### GET `/api/availability/<year>/<month>`
Retrieve availability data for a specific month.

**Response:**
```json
{
  "volunteers": {
    "John Smith": {
      "type": "N",
      "dates": [2, 3, 9, 10],
      "workload": 2,
      "updated": "2025-05-27T17:54:00"
    }
  }
}
```

### POST `/api/availability/<year>/<month>`
Save or update volunteer availability.

**Request Body:**
```json
{
  "name": "John Smith",
  "type": "N",
  "dates": [2, 3, 9, 10],
  "workload": 2
}
```

**Response:**
```json
{
  "success": true,
  "volunteer_existed": false,
  "message": "Availability saved successfully"
}
```

### GET `/api/availability/<year>/<month>/check/<name>`
Check if a volunteer already has availability saved.

**Response:**
```json
{
  "exists": true
}
```

## Data Storage

### File Structure
```
volunteer-availability/
├── availability/
│   ├── availability_2025_06.json
│   ├── availability_2025_07.json
│   └── ...
```

### Data Format
Each monthly file contains volunteer availability data:
```json
{
  "volunteers": {
    "Volunteer Name": {
      "type": "N|S|NS",
      "dates": [1, 2, 3, ...],
      "workload": 1-10,
      "updated": "ISO timestamp"
    }
  }
}
```

## Integration with Existing Systems

The application generates data compatible with existing volunteer scheduling systems. The saved data can be exported or accessed via the API for integration with roster generation tools.

### CSV Export Format
While the application saves to JSON, the data structure supports easy conversion to CSV:
```csv
Name,Type,Available days,Workload
John Smith,N,"2,3,9,10",2
Jane Doe,S,"4,5,11,12",1
```

## Browser Compatibility

- **Modern Browsers**: Chrome 60+, Firefox 55+, Safari 12+, Edge 79+
- **Mobile Support**: iOS Safari, Chrome Mobile, Samsung Internet
- **Features Used**: ES6 Classes, Fetch API, CSS Grid, Flexbox

## Troubleshooting

### Common Issues

1. **Calendar Not Loading**:
   - Ensure Flask server is running on port 5000
   - Check browser console for CORS errors
   - Verify month and year are selected

2. **Save Functionality Not Working**:
   - Confirm all required fields are filled
   - Check network connectivity to Flask server
   - Verify at least one date is selected

3. **Density Visualization Not Showing**:
   - Ensure existing data exists for the selected month
   - Check that volunteers have saved availability
   - Verify CSS classes are loading correctly

### Development Mode
For development, the Flask server runs with debug mode enabled. This provides:
- Automatic reloading on code changes
- Detailed error messages
- Debug toolbar (if installed)

## Security Considerations

- **Input Validation**: All user inputs are validated on both client and server
- **SQL Injection Prevention**: Uses JSON file storage (no SQL database)
- **XSS Protection**: User inputs are properly escaped
- **CORS Configuration**: Configured for local development (adjust for production)

## Future Enhancements

Potential improvements for future versions:
- Database integration (PostgreSQL, MySQL)
- User authentication and authorization
- Email notifications for availability updates
- Advanced reporting and analytics
- Mobile app development
- Integration with calendar systems (Google Calendar, Outlook)
- Bulk import/export functionality
- Advanced filtering and search capabilities

## License

This project is open source and available under the MIT License.

## Support

For technical support or feature requests, please refer to the project documentation or contact the development team.
