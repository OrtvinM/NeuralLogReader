const express = require('express');
const router = express.Router();
const detectorRoutes = require('./detector');

// Route to render the main page
router.get('/', (req, res) => {
    res.render('index'); // Ensure "index.ejs" is in the "views" folder
});

// Include the detector routes
router.use('/', detectorRoutes);

module.exports = router;
