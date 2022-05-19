const express = require("express");
const cors = require('cors');
const app = express();
const PORT = 8080;
const pageNotFound = 404;
const pageNotFoundMsg = "Page 404. Sorry can't find that!";
// const filesaver = require('file-saver')
const fs = require("fs")
// const ffmpeg = require('ffmpeg')
const ffmpeg = require('fluent-ffmpeg');
const {
    spawn
} = require('child_process');

// Set up Express
app.use(express.json())
app.use(express.urlencoded({
    extended: true
}));
app.use(cors({
    origin: "*",
}));

app.get('/cough/api', (req, res) => {
    res.end('Cough API is running')
})

app.post('/cough/api', (req, res) => {
    let msg = []
    req.on('data', (chunk) => {
        if (chunk) {
            msg.push(chunk)
        }
    })

    req.on('end', () => {
        let folder = Date.now().toString()
        let path = "file/" + folder
        let dir = path;
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir);
            fs.mkdirSync(dir + '/segmented_coughs');
        }
        path = path + '/'
        fs.writeFile(path + "cough_recording.webm", msg[0], (err) => {
            if (err) throw err;
            console.log('The file has been saved!');
            ffmpeg(path + "cough_recording.webm").output(path + 'cough.wav')
                .on('end', function () {
                    console.log('conversion ended');
                    runPython(res, path, folder)
                    // callback(null);
                }).on('error', function (err) {
                    console.log('error: ', err.code, err.msg);
                    // callback(err);
                }).run();
        });
    })
});

app.use((req, res) => {
    res.status(pageNotFound).send(pageNotFoundMsg);
});

app.listen(PORT);
console.log("Server started");


function runPython(res, path, folder) {
    console.log('===runPython===')
    const python = spawn('python', ['python/main.py', path]);
    let names = ""
    python.stdout.on('data', function (data) {
        // console.log('Pipe data from python script ...');
        data = data.toString().replace(/'/g, '"')
        names += data
    });

    python.on('close', (code) => {
        console.log(`python ended with code ${code}`);
        // send data to browser
        // res.send(dataToSend)
        console.log(names)
        names = JSON.parse(names)
        let result = {
            folder: folder,
            names: names
        }
        runPythonDataExtraction(res, folder, result)
    });
}


function runPythonDataExtraction(res, folder, result) {
    console.log('Python Extract data.json ...')
    const pythonExtract = spawn('python', ['python/extract_data.py', folder]);
    // console.log(folder)
    pythonExtract.stdout.on('data', function (data) {
        // console.log('Python Extract print...');
    });
    pythonExtract.on('close', (code) => {
        console.log(`PythonExtract ended with code ${code}`);
        runPrediction(res, folder, result)
    });

}

function runPrediction(res, folder, result) {
    console.log('Python Prediction ...')
    const pythonPred = spawn('python', ['python/prediction.py', folder]);
    let pred = ""
    pythonPred.stdout.on('data', function (data) {
        // console.log('pythonPred print ...');
        pred += data.toString()
    });
    pythonPred.on('close', (code) => {
        console.log(`pythonPred ended with code ${code}`);
        result['prediction'] = JSON.parse(pred)
        res.end(JSON.stringify(result))
    });
}


function deleteAllFiles(path) {
    console.log('deleting')
    fs.readdir(path, (err, files) => {
        if (err) throw err;
        for (const file of files) {
            fs.unlink(path + '/' + file, err => {
                if (err) throw err;
            });
        }
    });
}