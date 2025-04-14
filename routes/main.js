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
        return res.status(400).json({
            message: 'No file uploaded',
            errorCount: 0,
            normalizedText: "Error: No file provided."
        });
    }

    const filePath = req.file.path;
    const originalFileName = req.file.originalname;

    const pythonProcess = spawn('python', ['python/main.py']);

    let output = '';
    let errorOutput = '';

    // Send file and log type to Python
    pythonProcess.stdin.write(JSON.stringify({
        file: filePath,
        logType: originalFileName.toLowerCase().includes("ssh") ? "openssh" : "apache"
    }) + "\n");
    pythonProcess.stdin.end();

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
        fs.unlinkSync(filePath); // Clean up the uploaded file

        if (code === 0) {
            try {
                const resultPath = output.trim();
                const resultContent = fs.readFileSync(resultPath, 'utf-8');
                const result = JSON.parse(resultContent);
                fs.unlinkSync(resultPath); // Clean up temp result file

                res.json({
                    ...result,
                    downloadPath: result.downloadPath?.replace(/^.*results[\\/]/, 'downloads/')
                });
            } catch (e) {
                console.error("Error reading/parsing Python output:", e);
                res.status(500).json({
                    message: 'Failed to parse result from Python',
                    errorCount: 0,
                    normalizedText: "Error: Python output could not be parsed."
                });
            }
        } else {
            console.error(`Python script error: ${errorOutput}`);
            res.status(500).json({
                message: `Python script error: ${errorOutput}`,
                errorCount: 0,
                normalizedText: "Python processing failed."
            });
        }
    });

    pythonProcess.on('error', (err) => {
        console.error(`Failed to start Python process: ${err.message}`);
        res.status(500).json({
            message: 'Failed to start Python process',
            errorCount: 0,
            normalizedText: "Python execution failed."
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
