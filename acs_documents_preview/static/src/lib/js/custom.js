$(document).ready(function() {
    const instance = new CanvasSelect('#imageCanvas', '');

    // Set minimum dimensions and styles
    instance.MIN_WIDTH = 10;
    instance.MIN_HEIGHT = 10;
    instance.MIN_RADIUS = 5;
    instance.strokeStyle = '#0f0';
    instance.lineWidth = 1;
    instance.ctrlRadius = navigator.userAgent.includes('Mobile') ? 6 : 3;

    // Extending Medicine colors with new options
    const medicineColors = {
        "MedicineA": "#ff0000",
        "MedicineB": "#00ff00",
        "MedicineC": "#0000ff",
    };

    let currentMedicine = "";
    let currentDosage = "";
    let currentColor = "#000000";
    let actionsHistory = [];
    let logCounter = 0;

    const logContainer = document.getElementById('console-log');
    const medicineCounts = {};

    function addToLog(logData) {
        logCounter++;
        const logEntry = { index: logCounter, timestamp: new Date().toLocaleString(), data: logData };
        const logText = JSON.stringify(logEntry, null, 2);
        logContainer.innerHTML += logText + '\n\n';
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    // Canvas-select event listeners
    instance.on("load", (src) => console.log("image loaded", src));
    instance.on("delete", (info) => console.log("delete", info));
    instance.on("select", (shape) => console.log("select", shape));

    instance.on('add', (info) => {
        // Check if the dot tool is selected and if medicine and dosage have been chosen
        if (instance.createType === 3 && currentMedicine && currentDosage) {
            info.fillStyle = currentColor;
            info.label = `${currentDosage}`;
            const key = `${currentMedicine}-${currentDosage}`;
            medicineCounts[key] = (medicineCounts[key] || 0) + 1;
            updateCountTable();
            actionsHistory.push(info);
            instance.update();
            addToLog(`Added Shape: Type ${info.type}, Label: ${info.label}, Fill Style: ${info.fillStyle}`);
        }
    });
    

    function change(num) {
        instance.createType = num;
        if (num === 3) {
            $('#dosageSelection').removeClass('hidden');
            $('#dotToolButton').removeClass('hidden');
        }
        instance.update();
        addToLog(`Changed Create Type to ${num}`);
    }

    // Zoom functions
    function zoom(type) {
        instance.setScale(type);
    }

    function fitting() {
        instance.fitZoom();
    }

    // Button click handlers
    $('#zoomIn').click(() => zoom(true));
    $('#zoomOut').click(() => zoom(false));
    $('#fitting').click(fitting);
    $('#selectRectangle').click(() => change(1));
    $('#selectCircle').click(() => change(5));
    $('#selectDot').click(() => change(3));
    $('#editCanvas').click(() => change(0));
    $('#startSelection').click(() => $('#optionsPopup').toggleClass('hidden'));

    // Selection functions
    window.selectMedicine = function(medicine) {
        currentMedicine = medicine;
        currentColor = medicineColors[medicine] || "#000000";
        change(3); // Automatically switch to dot tool when a medicine is selected
        addToLog(`Selected Medicine: ${currentMedicine}, Color: ${currentColor}`);
    };
    
    window.selectDosage = function(dosage) {
        currentDosage = dosage;
        change(3); // Automatically switch to dot tool when a dosage is selected
        addToLog(`Selected Dosage: ${currentDosage}`);
    };
    

    function updateCountTable() {
        const tbody = $('#medicine-counts tbody');
        tbody.empty();
        Object.entries(medicineCounts).forEach(([key, count]) => {
            const [medicine, dosage] = key.split('-');
            tbody.append(`<tr><td>${medicine}</td><td>${dosage}</td><td>${count}</td></tr>`);
        });
    }

    // Popup toggle (if still needed)
    function togglePopup() {
        $('#optionsPopup').toggleClass('hidden');
    }

    // Dot tool activation (if needed)
    function activateDotTool() {
        change(3); // Ensure dot tool is selected
    }

    // Image loading
    $('.thumbnail-image').click(function() {
        const imageUrl = $(this).data('image');
        instance.setImage(imageUrl);
    });

    // Save image functionality
    $('#save_image').click(function() {
        const imageData = $('#imageCanvas')[0].toDataURL('image/png');
        $('#image_data').val(imageData);
        $(this).closest('form').submit();
    });
});
