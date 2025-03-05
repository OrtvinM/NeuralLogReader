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

router.post('/detect', (req, res) => {
    const { text } = req.body;

    if (!text || text.trim() === '') {
        return res.status(400).json({ message: 'No text provided', errorCount: 0 });
    }

    const pythonProcess = spawn('python', ['python/app.py', '--text']);

    let output = '';
    let errorOutput = '';

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
            res.status(500).json({ message: 'Python script error', errorCount: 0 });
        }
    });

    pythonProcess.stdin.write(text);
    pythonProcess.stdin.end();
});

// Execute Python script for file input
router.post('/detect-file', upload.single('file'), async (req, res) => {
    const filePath = req.file.path; 

    const pythonProcess = spawn('python', ['python/app.py', '--file', filePath]);

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
        fs.unlinkSync(filePath); // Clean up uploaded file
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
