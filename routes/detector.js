const express = require('express');
const router = express.Router();

router.post('/detect', (req, res) => {
    const { text } = req.body;

    if (!text) {
        return res.status(400).json({ message: 'No text provided', errorCount: 0 });
    }

    const errorKeywords = ["fatal", "error", "issue"];
    const errorCount = errorKeywords.filter(keyword => text.toLowerCase().includes(keyword)).length;

    res.json({ message: 'Received!', errorCount });
});

module.exports = router;
