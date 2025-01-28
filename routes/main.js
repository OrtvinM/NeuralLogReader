const express = require('express');
const router = express.Router();

// Route to render the main page
router.get('/', (req, res) => {
    res.render('index'); 
});

// Handle /detect route locally
router.post('/detect', (req, res) => {
    const { text } = req.body;

    if (!text) {
        return res.status(400).json({ message: 'No text provided', errorCount: 0 });
    }

    // Error detection logic
    const errorKeywords = ["fatal", "error", "issue"];
    const errorCount = errorKeywords.reduce((count, keyword) => {
        return count + (text.toLowerCase().split(keyword).length - 1);
    }, 0);

    res.json({ message: 'Received!', errorCount });
});

module.exports = router;
