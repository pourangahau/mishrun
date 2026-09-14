class VolunteerAvailabilityCalendar {
    constructor() {
        this.selectedDates = new Set();
        this.currentMonth = null;
        this.currentYear = null;
        this.availabilityData = {};
        this.apiBaseUrl = 'http://localhost:5000/api';
        
        this.initializeEventListeners();
        this.populateYearOptions();
    }

    initializeEventListeners() {
        document.getElementById('generateCalendar').addEventListener('click', () => this.generateCalendar());
        document.getElementById('clearAll').addEventListener('click', () => this.clearAllDates());
        document.getElementById('selectAll').addEventListener('click', () => this.selectAllDates());
        document.getElementById('saveData').addEventListener('click', () => this.saveAvailability());
    }

    populateYearOptions() {
        const yearSelect = document.getElementById('yearSelect');
        const currentYear = new Date().getFullYear();
        
        for (let year = currentYear; year <= currentYear + 3; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearSelect.appendChild(option);
        }
    }

    async generateCalendar() {
        const monthSelect = document.getElementById('monthSelect');
        const yearSelect = document.getElementById('yearSelect');
        
        if (!monthSelect.value || !yearSelect.value) {
            alert('Please select both month and year');
            return;
        }

        this.currentMonth = parseInt(monthSelect.value);
        this.currentYear = parseInt(yearSelect.value);
        
        // Load existing availability data
        await this.loadAvailabilityData();
        
        this.renderCalendar();
        this.showCalendarSection();
    }

    async loadAvailabilityData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/availability/${this.currentYear}/${this.currentMonth}`);
            if (response.ok) {
                const data = await response.json();
                this.availabilityData = data.volunteers || {};
            } else {
                this.availabilityData = {};
            }
        } catch (error) {
            console.error('Error loading availability data:', error);
            this.availabilityData = {};
        }
    }

    renderCalendar() {
        const calendar = document.getElementById('calendar');
        const calendarTitle = document.getElementById('calendarTitle');
        
        // Clear existing calendar
        calendar.innerHTML = '';
        
        // Set title
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December'];
        calendarTitle.textContent = `${monthNames[this.currentMonth - 1]} ${this.currentYear}`;
        
        // Create header
        const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        daysOfWeek.forEach(day => {
            const headerCell = document.createElement('div');
            headerCell.className = 'calendar-header';
            headerCell.textContent = day;
            calendar.appendChild(headerCell);
        });
        
        // Calculate calendar dates
        const firstDay = new Date(this.currentYear, this.currentMonth - 1, 1);
        const lastDay = new Date(this.currentYear, this.currentMonth, 0);
        const daysInMonth = lastDay.getDate();
        
        // Get first Monday (0 = Sunday, 1 = Monday, etc.)
        let startDate = new Date(firstDay);
        const dayOfWeek = firstDay.getDay();
        const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
        startDate.setDate(firstDay.getDate() + mondayOffset);
        
        // Generate calendar days (6 weeks)
        for (let week = 0; week < 6; week++) {
            for (let day = 0; day < 7; day++) {
                const currentDate = new Date(startDate);
                currentDate.setDate(startDate.getDate() + (week * 7) + day);
                
                const dayElement = this.createDayElement(currentDate);
                calendar.appendChild(dayElement);
            }
        }
        
        this.updateSelectedDatesDisplay();
    }

    createDayElement(date) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        
        const dayNumber = date.getDate();
        const isCurrentMonth = date.getMonth() === this.currentMonth - 1;
        const dayOfWeek = date.getDay();
        
        // Check if day should be disabled (Sat=6, Sun=0, Mon=1)
        const isDisabled = dayOfWeek === 0 || dayOfWeek === 1 || dayOfWeek === 6;
        
        if (!isCurrentMonth) {
            dayElement.classList.add('other-month');
        } else if (isDisabled) {
            dayElement.classList.add('disabled-day');
        }
        
        // Create day structure with split halves
        const dayContent = document.createElement('div');
        dayContent.className = 'day-content';
        
        const northHalf = document.createElement('div');
        northHalf.className = 'day-half north';
        
        const southHalf = document.createElement('div');
        southHalf.className = 'day-half south';
        
        const dayNumberElement = document.createElement('div');
        dayNumberElement.className = 'day-number';
        dayNumberElement.textContent = dayNumber;
        
        dayContent.appendChild(northHalf);
        dayContent.appendChild(southHalf);
        dayContent.appendChild(dayNumberElement);
        dayElement.appendChild(dayContent);
        
        // Apply density visualization if current month
        if (isCurrentMonth && !isDisabled) {
            this.applyDensityVisualization(dayElement, dayNumber, northHalf, southHalf);
            
            // Add click handler for selectable days
            dayElement.addEventListener('click', () => this.toggleDateSelection(dayNumber, dayElement));
        }
        
        return dayElement;
    }

    applyDensityVisualization(dayElement, dayNumber, northHalf, southHalf) {
        let northCount = 0;
        let southCount = 0;
        
        // Count volunteers for this date
        Object.values(this.availabilityData).forEach(volunteer => {
            if (volunteer.dates.includes(dayNumber)) {
                if (volunteer.type === 'N' || volunteer.type === 'NS') {
                    northCount++;
                }
                if (volunteer.type === 'S' || volunteer.type === 'NS') {
                    southCount++;
                }
            }
        });
        
        // Apply density classes (cap at 20)
        if (northCount > 0) {
            const densityLevel = Math.min(northCount, 20);
            northHalf.classList.add(`north-density-${densityLevel}`);
        }
        
        if (southCount > 0) {
            const densityLevel = Math.min(southCount, 20);
            southHalf.classList.add(`south-density-${densityLevel}`);
        }
    }

    toggleDateSelection(dayNumber, dayElement) {
        if (this.selectedDates.has(dayNumber)) {
            this.selectedDates.delete(dayNumber);
            dayElement.classList.remove('available');
        } else {
            this.selectedDates.add(dayNumber);
            dayElement.classList.add('available');
        }
        
        this.updateSelectedDatesDisplay();
    }

    clearAllDates() {
        this.selectedDates.clear();
        document.querySelectorAll('.calendar-day.available').forEach(day => {
            day.classList.remove('available');
        });
        this.updateSelectedDatesDisplay();
    }

    selectAllDates() {
        // Select all valid dates (Tue-Fri only)
        const daysInMonth = new Date(this.currentYear, this.currentMonth, 0).getDate();
        
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(this.currentYear, this.currentMonth - 1, day);
            const dayOfWeek = date.getDay();
            
            // Only select Tue(2), Wed(3), Thu(4), Fri(5)
            if (dayOfWeek >= 2 && dayOfWeek <= 5) {
                this.selectedDates.add(day);
            }
        }
        
        // Update visual state
        document.querySelectorAll('.calendar-day').forEach(dayElement => {
            const dayNumber = parseInt(dayElement.querySelector('.day-number')?.textContent);
            if (dayNumber && this.selectedDates.has(dayNumber)) {
                dayElement.classList.add('available');
            }
        });
        
        this.updateSelectedDatesDisplay();
    }

    updateSelectedDatesDisplay() {
        const selectedDatesElement = document.getElementById('selectedDates');
        
        if (this.selectedDates.size === 0) {
            selectedDatesElement.textContent = 'No dates selected';
        } else {
            const sortedDates = Array.from(this.selectedDates).sort((a, b) => a - b);
            selectedDatesElement.textContent = sortedDates.join(', ');
        }
    }

    async saveAvailability() {
        const name = document.getElementById('volunteerName').value.trim();
        const shiftType = document.getElementById('shiftType').value;
        const workload = parseInt(document.getElementById('workload').value);
        
        if (!name) {
            alert('Please enter your name');
            return;
        }
        
        if (!shiftType) {
            alert('Please select a shift type');
            return;
        }
        
        if (this.selectedDates.size === 0) {
            alert('Please select at least one available date');
            return;
        }
        
        // Check if volunteer already exists
        const existsResponse = await fetch(`${this.apiBaseUrl}/availability/${this.currentYear}/${this.currentMonth}/check/${encodeURIComponent(name)}`);
        if (existsResponse.ok) {
            const existsData = await existsResponse.json();
            if (existsData.exists) {
                const confirmed = confirm(`Do you want to overwrite the availability for ${name}?`);
                if (!confirmed) {
                    return;
                }
            }
        }
        
        // Prepare data
        const availabilityData = {
            name: name,
            type: shiftType,
            dates: Array.from(this.selectedDates).sort((a, b) => a - b),
            workload: workload
        };
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/availability/${this.currentYear}/${this.currentMonth}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(availabilityData)
            });
            
            if (response.ok) {
                const result = await response.json();
                alert('Availability saved successfully!');
                
                // Reload availability data and refresh calendar
                await this.loadAvailabilityData();
                this.renderCalendar();
            } else {
                const error = await response.json();
                alert(`Error saving availability: ${error.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error saving availability:', error);
            alert('Error saving availability. Please check if the server is running.');
        }
    }

    showCalendarSection() {
        document.getElementById('calendarSection').style.display = 'block';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VolunteerAvailabilityCalendar();
});
