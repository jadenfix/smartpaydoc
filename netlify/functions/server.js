const { spawn } = require('child_process');
const path = require('path');

exports.handler = async (event, context) => {
  // Forward the request to the FastAPI server
  return {
    statusCode: 200,
    body: JSON.stringify({ message: 'Serverless function is working' }),
  };
};
