const express = require('express');
const multer = require('multer');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const router = express.Router();
const upload = multer({ dest: 'uploads/' }); 

// Route to render the main page
router.get('/', (req, res) => {
    res.render('index'); 
});

// Handle file uploads and pass them to Python for processing
router.post('/detect-file', upload.single('file'), async (req, res) => {
    if (!req.file) {
        return res.status(400).json({ message: 'No file uploaded', errorCount: 0, normalizedText: "Error: No file provided." });
    }

    const filePath = req.file.path;
    const originalFileName = req.file.originalname;

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            console.error(`Error reading file: ${err}`);
            return res.status(500).json({ message: 'Error reading file', errorCount: 0, normalizedText: "Error: File could not be read." });
        }

        console.log(`Uploaded File: ${originalFileName}`);
        console.log("File Contents (Raw):");
        console.log(data);

        const pythonProcess = spawn('python', ['python/main.py']);

        let output = '';
        let errorOutput = '';

        pythonProcess.stdin.write(JSON.stringify({ file: filePath }) + "\n");
        pythonProcess.stdin.end();

        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });

        pythonProcess.on('close', (code) => {
            fs.unlinkSync(filePath);

            if (code === 0) {
                try {
                    // Ensure we only parse valid JSON
                    output = output.trim();
                    if (!output.startsWith('{')) {
                        console.error("Invalid JSON received from Python:", output);
                        return res.status(500).json({ message: "Invalid JSON response from Python", errorCount: 0, normalizedText: "Error: Unexpected Python output." });
                    }

                    const result = JSON.parse(output);
                    console.log("File Contents (Normalized):", result.normalizedText);
                    res.json(result);
                } catch (e) {
                    console.error('Error parsing Python output:', e, "Output received:", output);
                    res.status(500).json({ message: 'Error parsing Python output', errorCount: 0, normalizedText: "Error in parsing output." });
                }
            } else {
                console.error(`Python script error: ${errorOutput}`);
                res.status(500).json({ message: `Python script error: ${errorOutput}`, errorCount: 0, normalizedText: "Python processing failed." });
            }
        });

        pythonProcess.on('error', (err) => {
            console.error(`Failed to start Python process: ${err.message}`);
            res.status(500).json({ message: 'Failed to start Python process', errorCount: 0, normalizedText: "Python execution failed." });
        });
    });
});

// Handle text-based detection
router.post('/detect', async (req, res) => {
    const { text } = req.body;

    if (!text || text.trim() === '') {
        return res.status(400).json({ message: 'No text provided', errorCount: 0 });
    }

    const pythonProcess = spawn('python', ['python/main.py']);

    let output = '';
    let errorOutput = '';

    // Send text as JSON input to Python
    pythonProcess.stdin.write(JSON.stringify({ text: text }) + "\n");
    pythonProcess.stdin.end();

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (code === 0) {
            try {
                const result = JSON.parse(output.trim());
                res.json(result);
            } catch (e) {
                console.error('Error parsing Python output:', e);
                res.status(500).json({ message: 'Error parsing Python output', errorCount: 0 });
            }
        } else {
            console.error(`Python script error: ${errorOutput}`);
            res.status(500).json({ message: `Python script error: ${errorOutput}`, errorCount: 0 });
        }
    });

    pythonProcess.on('error', (err) => {
        console.error(`Failed to start Python process: ${err.message}`);
        res.status(500).json({ message: 'Failed to start Python process', errorCount: 0 });
    });
});

module.exports = router;
