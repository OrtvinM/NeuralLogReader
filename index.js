const express = require('express');
const ejs = require('ejs');

const app = express();
const port = 8000;

app.set('view engine', 'ejs');
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(__dirname + '/public'));
app.use('/downloads', express.static(__dirname + '/python/processing/results'));

app.locals.siteData = { siteName: "Log Reader" };

const mainRoutes = require('./routes/main');
app.use('/', mainRoutes);

app.listen(port, () => console.log(`Node app listening on port ${port}!`));
