const express = require('express');
const router = express.Router();

// Route to render the main page
router.get('/', (req, res) => {
    res.render('index'); // Ensure "index.ejs" is in the "views" folder
});

// Handle /detect route locally
router.post('/detect', (req, res) => {
    const { text } = req.body;

    if (!text) {
        return res.status(400).json({ message: 'No text provided', errorCount: 0 });
    }

    // Error detection logic (previously in Python)
    const errorKeywords = ["fatal", "error", "issue"];
    const errorCount = errorKeywords.reduce((count, keyword) => {
        return count + (text.toLowerCase().split(keyword).length - 1);
    }, 0);

    res.json({ message: 'Received!', errorCount });
});

module.exports = router;
